"""
===============================================================================
PageIndex Starter Script - Using Local Files with Azure OpenAI
===============================================================================

PURPOSE:
    This script demonstrates how to use PageIndex with a local .docx file
    using YOUR OWN Azure OpenAI deployment.
    
HOW IT WORKS:
    1. Loads Azure OpenAI API key from .env file
    2. Converts document to Markdown using a configurable strategy
    3. Generates a PageIndex tree structure using Azure OpenAI's GPT model
    4. Allows you to query the document using reasoning-based retrieval

CONVERSION STRATEGIES:
    - MARKITDOWN: Microsoft's MarkItDown library (recommended, fast)
    - LLM: Use GPT to convert each page (slower, better for complex docs)
    - SIMPLE: Basic python-docx extraction (fallback)

REQUIREMENTS:
    - Azure OpenAI API key in .env file as AZURE_OPENAI_API_KEY
    - markitdown (pip install markitdown) for MARKITDOWN strategy
    
INSTALL:
    pip install markitdown python-docx openai

===============================================================================
"""

import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import openai

# Import the converter system
from converters import ConversionStrategy, convert_document
from litellm import Router

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Load Environment Variables & Azure OpenAI Configuration
# ─────────────────────────────────────────────────────────────────────────────
# The load_dotenv() function reads the .env file in the project root
# and makes the variables available via os.getenv()
#
# ┌──────────────────────────────────────────────────────────────────────────┐
# │  AZURE OPENAI CONFIGURATION                                              │
# │                                                                          │
# │  Unlike regular OpenAI, Azure OpenAI uses:                               │
# │  - A custom endpoint URL (your Azure resource URL)                       │
# │  - A deployment name (instead of model name)                             │
# │  - The same API key format                                               │
# │                                                                          │
# │  The new OpenAI SDK (v1.x+) uses the base_url parameter to connect       │
# │  to Azure OpenAI, which simplifies the configuration.                    │
# └──────────────────────────────────────────────────────────────────────────┘
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Azure OpenAI Configuration
# ─────────────────────────────────────────────────────────────────────────────
# These values connect to your Azure OpenAI resource.
# The endpoint uses the new /openai/v1/ format which doesn't require api-version.
# ─────────────────────────────────────────────────────────────────────────────

# Azure OpenAI endpoint (with /openai/v1/ suffix for new SDK compatibility)
AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT", 
    "https://azure-openai-sponsorship-sweden.openai.azure.com/openai/v1/"
)

# Azure OpenAI deployment name (this is used instead of model name)
AZURE_DEPLOYMENT_NAME = os.getenv(
    "AZURE_DEPLOYMENT_NAME",
    "gpt-5.1-sponsorship"
)

# Azure OpenAI API Key
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("CHATGPT_API_KEY")

if not AZURE_OPENAI_API_KEY:
    raise ValueError(
        """
        ❌ ERROR: Azure OpenAI API key not found!
        
        Please create a .env file in the project root with:
        AZURE_OPENAI_API_KEY=your-azure-openai-key-here
        
        Or alternatively:
        OPENAI_API_KEY=your-azure-openai-key-here
        """
    )

print(f"✅ Azure OpenAI API key loaded (ending in ...{AZURE_OPENAI_API_KEY[-4:]})")
print(f"📍 Endpoint: {AZURE_OPENAI_ENDPOINT}")
print(f"🚀 Deployment: {AZURE_DEPLOYMENT_NAME}")

# ─────────────────────────────────────────────────────────────────────────────
# Create a centralized Azure OpenAI client
# ─────────────────────────────────────────────────────────────────────────────
# This client is used throughout the script for all LLM calls.
# Using base_url allows us to use the standard OpenAI SDK with Azure.
# ─────────────────────────────────────────────────────────────────────────────

OPENAI_CLIENT = openai.OpenAI(
    base_url=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY
)

# ─────────────────────────────────────────────────────────────────────────────
# Litellm Router Configuration
# ─────────────────────────────────────────────────────────────────────────────
model_list = [{
    "model_name": AZURE_DEPLOYMENT_NAME,
    "litellm_params": {
        "model": f"azure/{AZURE_DEPLOYMENT_NAME}",
        "api_key": AZURE_OPENAI_API_KEY,
        "base_url": AZURE_OPENAI_ENDPOINT,
        "tpm": 300000,
        "rpm": 1000
    }
}]

LLM_ROUTER = Router(model_list=model_list)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Configuration
# ─────────────────────────────────────────────────────────────────────────────
# Configure the document path and conversion strategy here.
# ─────────────────────────────────────────────────────────────────────────────

# Your local document file (supports DOCX, PDF, PPTX, etc.)
DOCUMENT_FILE_PATH = "/Users/jeroenverboom/PycharmProjects/PageIndex/Eteck_SLA_extractie_prompt.docx"

# Choose your conversion strategy:
#   - ConversionStrategy.MARKITDOWN  (recommended - fast, reliable)
#   - ConversionStrategy.LLM         (slower - uses GPT for conversion)
#   - ConversionStrategy.SIMPLE      (basic - only DOCX, limited formatting)
CONVERSION_STRATEGY = ConversionStrategy.MARKITDOWN

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2b: Tree Generation Strategy (NEW!)
# ─────────────────────────────────────────────────────────────────────────────
# Choose how to generate the document tree structure.
# ─────────────────────────────────────────────────────────────────────────────

from enum import Enum

class TreeGenerationStrategy(Enum):
    """
    Strategy for generating the document tree structure.
    
    ┌────────────────────────────────────────────────────────────────────────┐
    │  HEADER_PARSING (Fast, reliable, requires proper markdown headers)     │
    │  ──────────────────────────────────────────────────────────────────    │
    │  - Scans for # ## ### patterns in markdown                             │
    │  - Uses heading levels to build hierarchy                              │
    │  - Very fast (no LLM call for structure)                               │
    │  - Best for: Well-structured documents with clear headings             │
    │                                                                        │
    │  LLM (Slower, smarter, works on any document)                          │
    │  ──────────────────────────────────────────────────────────────────    │
    │  - Sends document to GPT with structured output                        │
    │  - LLM reasons about semantic sections                                 │
    │  - Works even without explicit headings                                │
    │  - Best for: Complex or unstructured documents                         │
    └────────────────────────────────────────────────────────────────────────┘
    """
    HEADER_PARSING = "header_parsing"  # Original method - parse markdown headers
    LLM = "llm"                        # New method - LLM with structured output

# Choose your tree generation strategy:
#   - TreeGenerationStrategy.HEADER_PARSING  (fast - parses markdown headers)
#   - TreeGenerationStrategy.LLM             (smart - uses GPT structured output)
TREE_GENERATION_STRATEGY = TreeGenerationStrategy.LLM


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Generate PageIndex Tree Structure
# ─────────────────────────────────────────────────────────────────────────────
# This uses PageIndex's local processing to create a hierarchical tree
# structure of your document using your Azure OpenAI deployment.

def generate_tree_from_markdown(md_path: str, model: str = None):
    """
    Generate a PageIndex tree structure from a Markdown file.
    
    WHAT THIS DOES:
    1. Uses OpenAI's LLM to analyze the document structure
    2. Creates a hierarchical "table of contents" style tree
    3. Each node contains: title, summary, page range, and child nodes
    
    HOW PAGEINDEX WORKS:
    - Unlike vector-based RAG, PageIndex doesn't chunk your document
    - Instead, it creates a tree structure based on semantic sections
    - Retrieval is done by "reasoning" through the tree, like a human expert
    
    Args:
        md_path: Path to the Markdown file
        model: Azure deployment name to use (default: AZURE_DEPLOYMENT_NAME)
        
    Returns:
        The generated tree structure as a dictionary
    """
    from pageindex.page_index_md import md_to_tree
    from pageindex.utils import ConfigLoader
    
    # Use Azure deployment name if no model specified
    if model is None:
        model = AZURE_DEPLOYMENT_NAME
    
    # Load configuration with defaults
    config_loader = ConfigLoader()
    opt = config_loader.load({
        'model': model,
        'if_add_node_summary': 'yes',
        'if_add_doc_description': 'yes',
        'if_add_node_text': 'yes',  # Include full text for retrieval
        'if_add_node_id': 'yes'
    })
    
    print(f"🔄 Generating PageIndex tree structure using model: {model}")
    print("   This may take a minute depending on document size...")
    
    # Run the async tree generation
    tree = asyncio.run(md_to_tree(
        md_path=md_path,
        if_thinning=False,
        min_token_threshold=5000,
        if_add_node_summary=opt.if_add_node_summary,
        summary_token_threshold=200,
        model=opt.model,
        if_add_doc_description=opt.if_add_doc_description,
        if_add_node_text=opt.if_add_node_text,
        if_add_node_id=opt.if_add_node_id
    ))
    
    print("✅ Tree structure generated successfully!")
    return tree


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: LLM-Based Tree Generation (Alternative Method)
# ─────────────────────────────────────────────────────────────────────────────
# This uses Azure OpenAI's structured output to generate the tree structure
# directly from the document, using reasoning instead of header parsing.
# ─────────────────────────────────────────────────────────────────────────────

def generate_tree_from_markdown_llm(md_path: str, model: str = None) -> dict:
    """
    Generate a PageIndex tree structure using LLM with structured output.
    
    ┌──────────────────────────────────────────────────────────────────────────┐
    │  HOW THIS DIFFERS FROM THE HEADER-PARSING METHOD                         │
    │                                                                          │
    │  HEADER-PARSING (generate_tree_from_markdown):                           │
    │  - Scans for # ## ### patterns in markdown                               │
    │  - Uses heading levels to build hierarchy                                │
    │  - Fast but ONLY works if document has proper headings                   │
    │                                                                          │
    │  LLM-BASED (this function):                                              │
    │  - Sends entire document to GPT                                          │
    │  - LLM reasons about semantic sections and structure                     │
    │  - Works on ANY document, even without explicit headings                 │
    │  - Slower but more flexible and "intelligent"                            │
    │                                                                          │
    │  Analogy:                                                                │
    │  - Header-parsing = Filing clerk sorting by labels on folders            │
    │  - LLM-based = Expert analyst who READS documents to organize them       │
    └──────────────────────────────────────────────────────────────────────────┘
    
    WHAT THIS DOES:
    1. Reads the markdown content
    2. Sends to GPT with structured output schema (Pydantic models)
    3. GPT returns a properly typed tree structure
    4. Returns the same format as generate_tree_from_markdown for drop-in replacement
    
    Args:
        md_path: Path to the Markdown file
        model: Azure deployment name to use (default: AZURE_DEPLOYMENT_NAME)
        
    Returns:
        The generated tree structure as a dictionary matching the PageIndex format:
        {
            "doc_name": str,
            "doc_description": str,
            "structure": [TreeNode, ...]
        }
    """
    import openai
    from pydantic import BaseModel, Field
    from typing import List, Optional
    
    # ─────────────────────────────────────────────────────────────────────────
    # Define Pydantic models for structured output
    # ─────────────────────────────────────────────────────────────────────────
    # These models define the EXACT structure that GPT must return.
    # OpenAI's structured output guarantees the response matches this schema.
    # 
    # ANALOGY: This is like giving GPT a very specific form to fill out,
    #          where each field has a defined type and purpose.
    # ─────────────────────────────────────────────────────────────────────────
    
    class TreeNode(BaseModel):
        """
        A single node in the document tree.
        
        WHAT EACH FIELD REPRESENTS:
        - title: The heading/name of this section (like a chapter title)
        - node_id: Unique identifier for retrieval (format: "0001", "0002", etc.)
        - summary: Brief description of what this section contains
        - text: The actual content of this section (full text)
        - line_num: Approximate line number where this section starts
        - nodes: Child sections nested under this one (recursive structure)
        """
        title: str = Field(
            description="The title or heading of this section. Should be concise and descriptive."
        )
        node_id: str = Field(
            description="Unique identifier in format '0001', '0002', etc. Sequential numbering."
        )
        summary: str = Field(
            description="A brief 1-3 sentence summary of what this section contains."
        )
        text: str = Field(
            description="The full text content of this section, including any subsection content."
        )
        line_num: int = Field(
            description="Approximate starting line number of this section in the original document."
        )
        nodes: Optional[List["TreeNode"]] = Field(
            default=None,
            description="Child nodes/subsections. None if this is a leaf node."
        )
    
    class DocumentTree(BaseModel):
        """
        The complete document tree structure.
        
        This is the root object that contains:
        - doc_name: Name of the document (usually filename without extension)
        - doc_description: Overall summary of what the document is about
        - structure: List of top-level sections, each potentially containing nested subsections
        """
        doc_name: str = Field(
            description="Name of the document, typically derived from the filename."
        )
        doc_description: str = Field(
            description="A comprehensive 2-4 sentence description of the entire document's purpose and content."
        )
        structure: List[TreeNode] = Field(
            description="List of top-level sections in the document. Each can have nested child nodes."
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Read the markdown content
    # ─────────────────────────────────────────────────────────────────────────
    with open(md_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Extract document name from file path
    doc_name = Path(md_path).stem
    
    # Count lines for reference
    total_lines = len(markdown_content.split('\n'))
    
    print(f"🤖 Generating tree structure using LLM with structured output...")
    print(f"   Model: {model}")
    print(f"   Document: {doc_name} ({total_lines} lines)")
    print(f"   This uses GPT to analyze document semantics, not just header patterns.")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Create the prompt for GPT
    # ─────────────────────────────────────────────────────────────────────────
    # We instruct GPT to:
    # 1. Analyze the document structure
    # 2. Identify logical sections (even without explicit headers)
    # 3. Create a hierarchical tree with proper nesting
    # 4. Generate summaries for each section
    # ─────────────────────────────────────────────────────────────────────────
    
    system_prompt = """You are a document structure analyst. Your task is to analyze the given document and create a hierarchical tree structure that represents its logical organization.

RULES FOR CREATING THE TREE:

1. IDENTIFY SECTIONS: Look for natural section breaks, even if there are no explicit headers.
   - Explicit headers (# ## ###) are strong section indicators
   - Topic changes, numbered lists, and paragraph breaks can also indicate sections
   
2. CREATE HIERARCHY: Organize sections in a parent-child relationship.
   - Top-level sections = major topics or chapters
   - Child sections = subtopics or subsections
   - Maximum depth: 4 levels (more depth creates harder navigation)
   
3. NODE IDs: Assign sequential IDs starting from "0001", "0002", etc.
   - Use depth-first ordering (parent comes before children)
   - Format: 4-digit zero-padded strings

4. SUMMARIES: Write concise summaries for each section.
   - 1-3 sentences maximum
   - Focus on WHAT the section contains, not interpretation
   - Use the document's own terminology

5. TEXT CONTENT: Include the FULL text of each section.
   - Include all content from that section's start to the next section
   - For parent nodes, only include intro text (not child content)
   
6. LINE NUMBERS: Estimate the starting line number for each section.
   - Line 1 = first line of document
   - Use best approximation based on content position

OUTPUT: Return a properly structured DocumentTree with all fields filled."""

    user_prompt = f"""Analyze this document and create a hierarchical tree structure:

DOCUMENT NAME: {doc_name}

DOCUMENT CONTENT:
{markdown_content}

Create a complete DocumentTree structure with:
- A descriptive doc_description (what is this document about?)
- A structure array with properly nested TreeNode objects
- Each node needs: title, node_id, summary, text, line_num, and optionally child nodes"""

    # ─────────────────────────────────────────────────────────────────────────
    # Call Azure OpenAI with structured output (using parse method)
    # ─────────────────────────────────────────────────────────────────────────
    # OpenAI's structured output feature uses Pydantic models to guarantee
    # the response matches our expected schema. No JSON parsing errors!
    # ─────────────────────────────────────────────────────────────────────────
    
    # Use Azure deployment name if no model specified
    if model is None:
        model = AZURE_DEPLOYMENT_NAME
    
    try:
        # Use the beta.chat.completions.parse method for structured output
        # This guarantees the response matches our DocumentTree schema
        # Use litellm Router completion
        # Note: We use the Router.completion method which handles the request distribution
        response = LLM_ROUTER.completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=DocumentTree,
        )
        
        # Extract the content and parse it using Pydantic
        # Litellm returns the JSON string in the content field when using response_format
        document_tree = DocumentTree.model_validate_json(response.choices[0].message.content)
        
        # Convert Pydantic model to dictionary for compatibility
        result = document_tree.model_dump()
        
        # ─────────────────────────────────────────────────────────────────────
        # Post-process: Ensure doc_name matches filename
        # ─────────────────────────────────────────────────────────────────────
        result['doc_name'] = doc_name
        
        # Clean up empty nodes arrays (convert None to missing key for compatibility)
        def clean_nodes(node_list):
            """Remove None nodes and empty nodes arrays for cleaner output."""
            if not node_list:
                return node_list
            for node in node_list:
                if node.get('nodes') is None or node.get('nodes') == []:
                    node.pop('nodes', None)
                else:
                    clean_nodes(node.get('nodes', []))
            return node_list
        
        result['structure'] = clean_nodes(result.get('structure', []))
        
        # Count nodes for logging
        def count_nodes(nodes):
            if not nodes:
                return 0
            count = len(nodes)
            for node in nodes:
                count += count_nodes(node.get('nodes', []))
            return count
        
        node_count = count_nodes(result.get('structure', []))
        print(f"✅ LLM tree structure generated successfully!")
        print(f"   Total nodes: {node_count}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error generating tree with LLM: {e}")
        raise


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: Query the Document Using Reasoning-Based Retrieval
# ─────────────────────────────────────────────────────────────────────────────
# This is the "RAG" part - we use the tree structure to find relevant
# sections and generate answers.
# ─────────────────────────────────────────────────────────────────────────────

async def query_document(tree: dict, query: str, model: str = None):
    """
    Query the document using reasoning-based retrieval.
    
    HOW THIS WORKS (Tree Search):
    1. We show the LLM the tree structure (like a table of contents)
    2. The LLM "reasons" about which sections are relevant to the query
    3. We extract the content from those sections
    4. We generate an answer based on the extracted content
    
    WHY THIS IS BETTER THAN VECTOR RAG:
    - Vector RAG finds "similar" content (which may not be "relevant")
    - PageIndex finds "relevant" content by reasoning (like a human expert)
    - You can trace exactly which sections the answer came from
    
    Args:
        tree: The PageIndex tree structure
        query: The user's question
        model: Azure deployment name to use (default: AZURE_DEPLOYMENT_NAME)
        
    Returns:
        A tuple of (answer, retrieved_nodes)
    """
    from pageindex.utils import structure_to_list
    
    # Use Azure deployment name if no model specified
    if model is None:
        model = AZURE_DEPLOYMENT_NAME
    
    # Create a node mapping for easy lookup
    nodes = structure_to_list(tree)
    node_map = {node.get('node_id', str(i)): node for i, node in enumerate(nodes)}
    
    # Remove full text from tree for the search prompt (to fit in context)
    def remove_text(data):
        if isinstance(data, dict):
            return {k: remove_text(v) for k, v in data.items() if k != 'text'}
        elif isinstance(data, list):
            return [remove_text(item) for item in data]
        return data
    
    tree_without_text = remove_text(tree)
    
    # ─────────────────────────────────────────────────────────────────────
    # Step 5.1: Tree Search - Find relevant nodes
    # ─────────────────────────────────────────────────────────────────────
    search_prompt = f"""
You are given a question and a tree structure of a document.
Each node contains a node id, node title, and a corresponding summary.
Your task is to find all nodes that are likely to contain the answer to the question.

Question: {query}

Document tree structure:
{json.dumps(tree_without_text, indent=2)}

Please reply in the following JSON format:
{{
    "thinking": "<Your thinking process on which nodes are relevant to the question>",
    "node_list": ["node_id_1", "node_id_2", ..., "node_id_n"]
}}
Directly return the final JSON structure. Do not output anything else.
"""
    
    print(f"\n🔍 Searching document for: '{query}'")
    
    response = LLM_ROUTER.completion(
        model=model,
        messages=[{"role": "user", "content": search_prompt}],
        # temperature=0
    )
    
    search_result = json.loads(response.choices[0].message.content.strip())
    
    print(f"\n💭 Reasoning: {search_result['thinking'][:200]}...")
    print(f"\n📑 Found {len(search_result['node_list'])} relevant section(s)")
    
    # ─────────────────────────────────────────────────────────────────────
    # Step 5.2: Extract content from relevant nodes
    # ─────────────────────────────────────────────────────────────────────
    relevant_content = []
    for node_id in search_result['node_list']:
        if node_id in node_map:
            node = node_map[node_id]
            content = node.get('text', node.get('summary', ''))
            relevant_content.append(f"### {node.get('title', 'Section')}\n{content}")
            print(f"   - Node {node_id}: {node.get('title', 'Untitled')}")
    
    # ─────────────────────────────────────────────────────────────────────
    # Step 5.3: Generate answer based on retrieved content
    # ─────────────────────────────────────────────────────────────────────
    context = "\n\n".join(relevant_content)
    
    answer_prompt = f"""
Answer the question based on the context provided.

Question: {query}

Context:
{context}

Provide a clear, concise answer based only on the context provided.
If the context doesn't contain enough information to answer, say so.
"""
    
    print(f"\n📝 Generating answer...")
    
    response = LLM_ROUTER.completion(
        model=model,
        messages=[{"role": "user", "content": answer_prompt}],
        temperature=0
    )
    
    answer = response.choices[0].message.content.strip()
    
    return answer, search_result


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """
    Main execution flow:
    1. Convert document to Markdown using the configured strategy
    2. Generate PageIndex tree structure
    3. Allow interactive querying
    """
    print("\n" + "="*70)
    print("🚀 PageIndex Starter Script - Using Local Files with OpenAI")
    print("="*70 + "\n")
    
    # Check if file exists
    if not os.path.exists(DOCUMENT_FILE_PATH):
        raise FileNotFoundError(f"File not found: {DOCUMENT_FILE_PATH}")
    
    print(f"📄 Processing file: {DOCUMENT_FILE_PATH}")
    print(f"📋 Conversion strategy: {CONVERSION_STRATEGY.value}")
    print(f"🌲 Tree generation: {TREE_GENERATION_STRATEGY.value}")
    
    # ─────────────────────────────────────────────────────────────────────
    # Convert Document to Markdown using the configured strategy
    # ─────────────────────────────────────────────────────────────────────
    base_name = Path(DOCUMENT_FILE_PATH).stem
    md_file_path = Path(DOCUMENT_FILE_PATH).parent / f"{base_name}.md"
    
    print(f"\n📝 Step 1: Converting document to Markdown...")
    
    # Use the converter system - pass API key for LLM strategy
    convert_document(
        file_path=DOCUMENT_FILE_PATH,
        output_path=str(md_file_path),
        strategy=CONVERSION_STRATEGY,
        api_key=OPENAI_API_KEY if CONVERSION_STRATEGY == ConversionStrategy.LLM else None
    )
    
    # ─────────────────────────────────────────────────────────────────────
    # Generate PageIndex Tree Structure using the configured strategy
    # ─────────────────────────────────────────────────────────────────────
    print("\n🌲 Step 2: Generating PageIndex tree structure...")
    
    # Choose tree generation method based on configuration
    # ─────────────────────────────────────────────────────────────────────
    # HEADER_PARSING: Fast, uses markdown header patterns (# ## ###)
    # LLM: Slower but smarter, uses GPT structured output
    # ─────────────────────────────────────────────────────────────────────
    if TREE_GENERATION_STRATEGY == TreeGenerationStrategy.HEADER_PARSING:
        # Original method: parse markdown headers
        tree = generate_tree_from_markdown(str(md_file_path))
    else:
        # New method: LLM with structured output
        tree = generate_tree_from_markdown_llm(str(md_file_path))
    
    # Save tree to JSON for inspection
    tree_output_path = Path(DOCUMENT_FILE_PATH).parent / f"{base_name}_tree.json"
    with open(tree_output_path, "w", encoding="utf-8") as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)
    print(f"💾 Tree structure saved to: {tree_output_path}")
    
    # ─────────────────────────────────────────────────────────────────────
    # Interactive Query Loop
    # ─────────────────────────────────────────────────────────────────────
    print("\n" + "="*70)
    print("💬 Document ready for queries!")
    print("   Type your question and press Enter.")
    print("   Type 'quit' or 'exit' to stop.")
    print("="*70)
    
    while True:
        try:
            query = input("\n❓ Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not query:
                print("Please enter a question.")
                continue
            
            # Query the document
            answer, search_result = asyncio.run(query_document(tree, query))
            
            print("\n" + "-"*70)
            print("📖 ANSWER:")
            print("-"*70)
            print(answer)
            print("-"*70)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
