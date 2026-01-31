# PageIndex Tree: Creation & Retrieval Explained

> A beginner-friendly guide to understand how PageIndex creates hierarchical tree structures from documents and how it retrieves information using reasoning-based navigation.

---

## The Problem

Traditional RAG (Retrieval-Augmented Generation) systems **chunk documents blindly** - splitting them into equal-sized pieces like cutting a book into random 500-word slices. This loses the **semantic meaning** and **natural structure** of the document.

| Traditional RAG Problem | Real-World Analogy |
|-------------------------|-------------------|
| Blindly chunks text     | Cutting a recipe book into random paragraphs, mixing "Ingredients" with "Instructions" |
| Finds "similar" text    | Google showing pages that contain your keywords, but not answering your question |
| No understanding of structure | Looking for a chapter in a book by flipping random pages |

---

## The Analogy: 📚 A Library Expert

Imagine you have a **library expert** helping you find information. You wouldn't want them to:
- ❌ Randomly flip through pages looking for keyword matches
- ❌ Cut the book into puzzle pieces and find the most similar piece

Instead, you'd want them to:
- ✅ Look at the **Table of Contents** first
- ✅ **Reason** about which chapter or section would contain the answer
- ✅ Navigate to the **exact section** and read it carefully

**PageIndex works like this library expert!**

---

## Part 1: Tree Creation (Building the Table of Contents)

### The Real-World Analogy: 🏢 Building a Company Org Chart

Think of creating the tree like drawing an **organizational chart** of a company from a list of employees:

| Document Structure | Company Org Chart |
|--------------------|-------------------|
| `# Heading 1`      | CEO               |
| `## Heading 2`     | VP / Director     |
| `### Heading 3`    | Manager           |
| `#### Heading 4`   | Team Lead         |
| Content under heading | Employee's responsibilities |

### The Creation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TREE CREATION PIPELINE                                  │
│                                                                             │
│   📄 Document (DOCX/PDF)                                                    │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────┐                               │
│   │  STEP 1: Convert to Markdown            │                               │
│   │  ─────────────────────────────────────  │                               │
│   │  # Headings become tree nodes           │                               │
│   │  Content becomes node text              │                               │
│   └─────────────────────────────────────────┘                               │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────┐                               │
│   │  STEP 2: Extract Nodes from Headers     │                               │
│   │  ─────────────────────────────────────  │                               │
│   │  Scan for # ## ### #### patterns        │                               │
│   │  Record: title, level, line_number      │                               │
│   └─────────────────────────────────────────┘                               │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────┐                               │
│   │  STEP 3: Attach Text Content            │                               │
│   │  ─────────────────────────────────────  │                               │
│   │  For each node, capture all text        │                               │
│   │  from this header to the next one       │                               │
│   └─────────────────────────────────────────┘                               │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────┐                               │
│   │  STEP 4: Build Hierarchical Tree        │                               │
│   │  ─────────────────────────────────────  │                               │
│   │  Use heading levels to determine        │                               │
│   │  parent-child relationships             │                               │
│   └─────────────────────────────────────────┘                               │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────┐                               │
│   │  STEP 5: Generate AI Summaries          │                               │
│   │  ─────────────────────────────────────  │                               │
│   │  LLM creates brief summary for each     │                               │
│   │  node (optional but recommended)        │                               │
│   └─────────────────────────────────────────┘                               │
│         │                                                                   │
│         ▼                                                                   │
│   🌲 Final Tree Structure (JSON)                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step-by-Step Deep Dive

#### Step 1: Convert Document to Markdown

```
┌──────────────────────────────────────────────────────────────────┐
│  INPUT: DOCX/PDF Document                                        │
│                                                                  │
│  ┌────────────────────────┐      ┌────────────────────────────┐  │
│  │                        │      │                            │  │
│  │  [Bold Title Style]   │  ──▶ │  # Title                   │  │
│  │                        │      │                            │  │
│  │  [Heading 1 Style]    │  ──▶ │  # Heading 1               │  │
│  │                        │      │                            │  │
│  │  [Heading 2 Style]    │  ──▶ │  ## Heading 2              │  │
│  │                        │      │                            │  │
│  │  Normal text here...  │  ──▶ │  Normal text here...       │  │
│  │                        │      │                            │  │
│  └────────────────────────┘      └────────────────────────────┘  │
│       DOCX File                       Markdown File              │
│                                                                  │
│  WHY: The "#" symbols tell us the LEVEL of each section         │
│       This is like detecting "manager", "director", "CEO"       │
│       from someone's title format on their business card        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

#### Step 2 & 3: Extract Nodes and Attach Text

**Analogy**: Like a librarian creating catalog cards for each chapter

```
┌──────────────────────────────────────────────────────────────────┐
│  PARSING THE MARKDOWN                                            │
│                                                                  │
│  Line 1:  # Company Overview          ──▶  Node 1, Level 1       │
│  Line 2:  Our company was founded...  ──▶  (content for Node 1)  │
│  Line 3:  We specialize in...         ──▶  (content for Node 1)  │
│  Line 4:  ## Products                 ──▶  Node 2, Level 2       │
│  Line 5:  We sell widgets...          ──▶  (content for Node 2)  │
│  Line 6:  ### Widget A                ──▶  Node 3, Level 3       │
│  Line 7:  Widget A is blue...         ──▶  (content for Node 3)  │
│  Line 8:  ### Widget B                ──▶  Node 4, Level 3       │
│  Line 9:  Widget B is red...          ──▶  (content for Node 4)  │
│  Line 10: ## Services                 ──▶  Node 5, Level 2       │
│  Line 11: We offer consulting...      ──▶  (content for Node 5)  │
│                                                                  │
│  RESULT: A list of nodes                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ node_list = [                                              │  │
│  │   {title: "Company Overview", level: 1, line: 1},          │  │
│  │   {title: "Products",         level: 2, line: 4},          │  │
│  │   {title: "Widget A",         level: 3, line: 6},          │  │
│  │   {title: "Widget B",         level: 3, line: 8},          │  │
│  │   {title: "Services",         level: 2, line: 10},         │  │
│  │ ]                                                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

#### Step 4: Build Hierarchical Tree (The Magic!)

**Analogy**: Assembling a family tree from birth certificates

The algorithm uses a **stack** (like a stack of plates) to track the current path in the tree:

```
┌──────────────────────────────────────────────────────────────────┐
│  BUILDING THE TREE WITH A STACK                                  │
│                                                                  │
│  Processing "Company Overview" (Level 1):                        │
│  Stack: [ ]  ──▶  Stack: [ Company Overview (L1) ]               │
│                                                                  │
│    Result:  🌳 Company Overview                                  │
│                                                                  │
│  ─────────────────────────────────────────────────────────────── │
│                                                                  │
│  Processing "Products" (Level 2):                                │
│  Stack: [ Company Overview (L1) ]                                │
│    ↳ Level 2 > Level 1, so "Products" is CHILD of top of stack  │
│  Stack: [ Company Overview (L1), Products (L2) ]                 │
│                                                                  │
│    Result:  🌳 Company Overview                                  │
│              └── Products                                        │
│                                                                  │
│  ─────────────────────────────────────────────────────────────── │
│                                                                  │
│  Processing "Widget A" (Level 3):                                │
│  Stack: [ Company Overview (L1), Products (L2) ]                 │
│    ↳ Level 3 > Level 2, so "Widget A" is CHILD of Products      │
│  Stack: [ Company Overview (L1), Products (L2), Widget A (L3) ]  │
│                                                                  │
│    Result:  🌳 Company Overview                                  │
│              └── Products                                        │
│                   └── Widget A                                   │
│                                                                  │
│  ─────────────────────────────────────────────────────────────── │
│                                                                  │
│  Processing "Widget B" (Level 3):                                │
│  Stack: [ Company Overview (L1), Products (L2), Widget A (L3) ]  │
│    ↳ Level 3 = Level 3, so POP Widget A first (sibling!)        │
│  Stack: [ Company Overview (L1), Products (L2) ]                 │
│    ↳ Now add Widget B as child of Products                       │
│  Stack: [ Company Overview (L1), Products (L2), Widget B (L3) ]  │
│                                                                  │
│    Result:  🌳 Company Overview                                  │
│              └── Products                                        │
│                   ├── Widget A                                   │
│                   └── Widget B                                   │
│                                                                  │
│  ─────────────────────────────────────────────────────────────── │
│                                                                  │
│  Processing "Services" (Level 2):                                │
│  Stack: [ Company Overview (L1), Products (L2), Widget B (L3) ]  │
│    ↳ Level 2 = Level of Products, so POP until we find parent   │
│  Stack: [ Company Overview (L1) ]                                │
│    ↳ Now add Services as child of Company Overview               │
│  Stack: [ Company Overview (L1), Services (L2) ]                 │
│                                                                  │
│    Result:  🌳 Company Overview                                  │
│              ├── Products                                        │
│              │    ├── Widget A                                   │
│              │    └── Widget B                                   │
│              └── Services                                        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

#### Final Tree Structure (JSON Output)

```json
{
  "doc_name": "Company_Document",
  "structure": [
    {
      "title": "Company Overview",
      "node_id": "0001",
      "summary": "Overview of company history and mission",
      "nodes": [
        {
          "title": "Products",
          "node_id": "0002",
          "summary": "Product catalog including widgets",
          "nodes": [
            {
              "title": "Widget A",
              "node_id": "0003",
              "summary": "Blue widget details and pricing"
            },
            {
              "title": "Widget B", 
              "node_id": "0004",
              "summary": "Red widget details and pricing"
            }
          ]
        },
        {
          "title": "Services",
          "node_id": "0005", 
          "summary": "Consulting and support services"
        }
      ]
    }
  ]
}
```

---

## Part 2: Tree Retrieval (Finding the Answer)

### The Real-World Analogy: 🔍 Expert Research Assistant

Imagine asking a **research librarian** to find information:

| Step | Librarian Behavior | PageIndex Behavior |
|------|-------------------|-------------------|
| 1 | Reads your question carefully | Receives user query |
| 2 | Pulls out the Table of Contents | Shows tree structure to LLM |
| 3 | Thinks: "This topic is probably in Chapter 3, Section 2.1" | LLM reasons about which nodes are relevant |
| 4 | Walks to the shelf and pulls out those sections | Retrieves text content from selected nodes |
| 5 | Reads the content and formulates an answer | LLM generates answer from retrieved content |

### The Retrieval Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TREE RETRIEVAL PIPELINE                                 │
│                                                                             │
│   ❓ User Question: "What color is Widget A?"                               │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 1: Prepare Tree for Navigation                                │   │
│   │  ───────────────────────────────────────────────────────────────    │   │
│   │                                                                     │   │
│   │  Remove full text content (too long for context window)             │   │
│   │  Keep: title, node_id, summary                                      │   │
│   │                                                                     │   │
│   │  ┌─────────────────────────────────────────┐                        │   │
│   │  │  Tree (for LLM to see):                 │                        │   │
│   │  │                                         │                        │   │
│   │  │  📁 Company Overview (0001)             │                        │   │
│   │  │     Summary: "Overview of company..."   │                        │   │
│   │  │     ├── 📁 Products (0002)              │                        │   │
│   │  │     │      Summary: "Product catalog.." │                        │   │
│   │  │     │      ├── 📄 Widget A (0003)       │  ◀── LIKELY RELEVANT!  │   │
│   │  │     │      │      Summary: "Blue widget"│                        │   │
│   │  │     │      └── 📄 Widget B (0004)       │                        │   │
│   │  │     │             Summary: "Red widget" │                        │   │
│   │  │     └── 📁 Services (0005)              │                        │   │
│   │  │            Summary: "Consulting..."     │                        │   │
│   │  └─────────────────────────────────────────┘                        │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 2: LLM Reasons About Relevant Nodes (Tree Search)             │   │
│   │  ───────────────────────────────────────────────────────────────    │   │
│   │                                                                     │   │
│   │  🤖 LLM Prompt:                                                     │   │
│   │  "Given this tree structure and the question 'What color is        │   │
│   │   Widget A?', which nodes are likely to contain the answer?"        │   │
│   │                                                                     │   │
│   │  🧠 LLM Thinking:                                                   │   │
│   │  "The question asks about Widget A's color.                         │   │
│   │   Looking at the tree, I see node 0003 is titled 'Widget A'         │   │
│   │   and its summary mentions 'Blue widget'.                           │   │
│   │   This is clearly the relevant section."                            │   │
│   │                                                                     │   │
│   │  📤 LLM Output:                                                     │   │
│   │  {                                                                  │   │
│   │    "thinking": "Widget A is explicitly about the widget...",        │   │
│   │    "node_list": ["0003"]                                            │   │
│   │  }                                                                  │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 3: Extract Content from Selected Nodes                        │   │
│   │  ───────────────────────────────────────────────────────────────    │   │
│   │                                                                     │   │
│   │  node_map["0003"] = {                                               │   │
│   │    "title": "Widget A",                                             │   │
│   │    "text": "### Widget A\nWidget A is our flagship product.\n       │   │
│   │             It comes in a beautiful BLUE color and is made\n        │   │
│   │             of high-quality materials. Price: $49.99"               │   │
│   │  }                                                                  │   │
│   │                                                                     │   │
│   │  Retrieved Content:                                                 │   │
│   │  ┌────────────────────────────────────────────┐                     │   │
│   │  │ ### Widget A                               │                     │   │
│   │  │ Widget A is our flagship product.          │                     │   │
│   │  │ It comes in a beautiful BLUE color...      │                     │   │
│   │  └────────────────────────────────────────────┘                     │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 4: Generate Final Answer                                       │   │
│   │  ───────────────────────────────────────────────────────────────    │   │
│   │                                                                     │   │
│   │  🤖 LLM Prompt:                                                     │   │
│   │  "Answer the question based on this context:                        │   │
│   │   Question: What color is Widget A?                                 │   │
│   │   Context: ### Widget A\nWidget A is... BLUE color..."              │   │
│   │                                                                     │   │
│   │  📤 LLM Answer:                                                     │   │
│   │  "Widget A comes in a blue color."                                  │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│   ✅ Answer: "Widget A comes in a blue color."                             │
│      Source: Node 0003 (Widget A)                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why This is Better Than Traditional RAG

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                 PAGEINDEX vs TRADITIONAL RAG                                  │
│                                                                              │
│  ┌────────────────────────────────┐    ┌────────────────────────────────┐    │
│  │      TRADITIONAL RAG           │    │        PAGEINDEX               │    │
│  │                                │    │                                │    │
│  │  📄 Document                   │    │  📄 Document                   │    │
│  │       │                        │    │       │                        │    │
│  │       ▼                        │    │       ▼                        │    │
│  │  ✂️  Chunk blindly             │    │  🌲 Build semantic tree        │    │
│  │  [chunk1][chunk2][chunk3]...   │    │  (preserves structure)         │    │
│  │       │                        │    │       │                        │    │
│  │       ▼                        │    │       ▼                        │    │
│  │  🔢 Convert to vectors         │    │  📝 Generate node summaries    │    │
│  │  [0.1, 0.3, ...][0.2, 0.4...] │    │  (LLM understands each part)   │    │
│  │       │                        │    │       │                        │    │
│  │       ▼                        │    │       ▼                        │    │
│  │  🎯 Find similar vectors       │    │  🧠 LLM reasons about query    │    │
│  │  (cosine similarity search)    │    │  (like a human expert)         │    │
│  │       │                        │    │       │                        │    │
│  │       ▼                        │    │       ▼                        │    │
│  │  ❓ Might miss context!        │    │  ✅ Finds semantically correct │    │
│  │     "Widget" ≈ "Gadget"?       │    │     sections every time        │    │
│  │                                │    │                                │    │
│  └────────────────────────────────┘    └────────────────────────────────┘    │
│                                                                              │
│  Real-World Analogy:                                                         │
│                                                                              │
│  Traditional RAG = Using a metal detector to find a specific coin           │
│                    in a pile of random metal objects                         │
│                    (finds similar metal, not necessarily the coin you want)  │
│                                                                              │
│  PageIndex = Having a coin collector who knows exactly which drawer          │
│              each type of coin is organized in                               │
│              (knows WHERE to look, not just what looks similar)              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Bonus: Two Ways to Build the Tree

PageIndex now supports **two different methods** for creating the tree structure:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│           TWO TREE GENERATION STRATEGIES                                      │
│                                                                              │
│  ┌────────────────────────────────┐    ┌────────────────────────────────┐    │
│  │   HEADER PARSING (Fast)        │    │      LLM-BASED (Smart)         │    │
│  │                                │    │                                │    │
│  │  📝 How it works:              │    │  🤖 How it works:              │    │
│  │  - Scans for # ## ### ####     │    │  - Sends doc to GPT            │    │
│  │  - Uses heading levels         │    │  - Uses structured output      │    │
│  │  - Builds tree from patterns   │    │  - LLM reasons about structure │    │
│  │                                │    │                                │    │
│  │  ⚡ Speed: Very fast            │    │  ⚡ Speed: Slower (LLM call)    │    │
│  │                                │    │                                │    │
│  │  ✅ Best for:                   │    │  ✅ Best for:                   │    │
│  │  - Well-formatted docs         │    │  - Messy documents             │    │
│  │  - Clear heading structure     │    │  - No explicit headings        │    │
│  │  - Technical documentation     │    │  - Complex nested content      │    │
│  │                                │    │                                │    │
│  │  ❌ Limitations:                │    │  ❌ Limitations:                │    │
│  │  - Requires proper headers     │    │  - Slower (LLM API call)       │    │
│  │  - May miss semantic groups    │    │  - Costs tokens                │    │
│  │                                │    │                                │    │
│  └────────────────────────────────┘    └────────────────────────────────┘    │
│                                                                              │
│  Analogy:                                                                    │
│  ────────                                                                    │
│  HEADER PARSING = Filing clerk who sorts by folder labels                   │
│                   (Fast, but only works if labels are correct)              │
│                                                                              │
│  LLM-BASED = Expert analyst who READS the content to organize it            │
│              (Slower, but understands meaning, not just formatting)         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### How to Switch Between Methods

In `starter_script.py`, change the configuration:

```python
# For fast header-based parsing (default):
TREE_GENERATION_STRATEGY = TreeGenerationStrategy.HEADER_PARSING

# For smart LLM-based analysis:
TREE_GENERATION_STRATEGY = TreeGenerationStrategy.LLM
```

### LLM-Based Tree Generation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  LLM-BASED TREE GENERATION                                   │
│                                                                             │
│   📄 Markdown Document                                                      │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 1: Define Pydantic Schema                                     │   │
│   │  ───────────────────────────────────────────────────────────────    │   │
│   │                                                                     │   │
│   │  class TreeNode(BaseModel):                                         │   │
│   │      title: str                                                     │   │
│   │      node_id: str        # "0001", "0002", etc.                     │   │
│   │      summary: str        # Brief description                        │   │
│   │      text: str           # Full content                             │   │
│   │      line_num: int       # Starting line                            │   │
│   │      nodes: List[TreeNode]  # Children (recursive!)                 │   │
│   │                                                                     │   │
│   │  class DocumentTree(BaseModel):                                     │   │
│   │      doc_name: str                                                  │   │
│   │      doc_description: str                                           │   │
│   │      structure: List[TreeNode]                                      │   │
│   │                                                                     │   │
│   │  WHY: This ensures GPT returns EXACTLY the format we need           │   │
│   │       No JSON parsing errors, no missing fields!                    │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 2: Send to GPT with Structured Output                         │   │
│   │  ───────────────────────────────────────────────────────────────    │   │
│   │                                                                     │   │
│   │  client.beta.chat.completions.parse(                                │   │
│   │      model="gpt-4.1",                                               │   │
│   │      messages=[system_prompt, user_prompt],                         │   │
│   │      response_format=DocumentTree,  # ← Magic: guarantees schema!  │   │
│   │  )                                                                  │   │
│   │                                                                     │   │
│   │  GPT analyzes the document and returns a properly typed tree        │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  STEP 3: GPT Reasons About Document Structure                       │   │
│   │  ───────────────────────────────────────────────────────────────    │   │
│   │                                                                     │   │
│   │  🧠 GPT thinking:                                                   │   │
│   │  "This document has 8 main sections based on the ## headers.        │   │
│   │   Section 2 has multiple sub-points that should be child nodes.     │   │
│   │   The 'Extra' section at the end is a standalone leaf node..."      │   │
│   │                                                                     │   │
│   │  Unlike header-parsing, GPT can:                                    │   │
│   │  - Identify sections even without explicit headers                  │   │
│   │  - Group related content logically                                  │   │
│   │  - Generate meaningful summaries automatically                      │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│         │                                                                   │
│         ▼                                                                   │
│   🌲 Complete DocumentTree (same format as header-parsing!)                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary: Key Takeaways

1. **Tree Creation** reads document headers (`#`, `##`, `###`) to automatically build a **hierarchical structure** - like creating a Table of Contents from a book.

2. **The Stack Algorithm** determines parent-child relationships by tracking heading levels - lower numbers are parents, higher numbers are children.

3. **Node Summaries** are generated by an LLM to provide quick descriptions of each section without including the full text.

4. **Tree Retrieval** works by showing the LLM the "Table of Contents" and asking it to **reason** about which sections are relevant.

5. **Reasoning beats Similarity**: Instead of finding "similar" content (which might be wrong), PageIndex finds **logically relevant** content (like a human expert would).

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `pageindex/page_index_md.py` | Core tree creation logic (markdown → tree via header parsing) |
| `pageindex/utils.py` | Helper functions for tree manipulation |
| `starter_script.py` | Example script showing creation + retrieval |

### Functions in `starter_script.py`

| Function | Method | Description |
|----------|--------|-------------|
| `generate_tree_from_markdown()` | Header Parsing | Fast, scans for `# ## ###` patterns |
| `generate_tree_from_markdown_llm()` | LLM Structured Output | Smart, uses GPT to reason about structure |
| `query_document()` | Tree Retrieval | Uses LLM to find relevant nodes and answer questions |

---

## Visual Memory Aid

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                                                                         │
 │   📄 DOCUMENT  ──────────▶  🌲 TREE  ──────────▶  ❓ QUERY              │
 │                                                                         │
 │   "Convert"                "Build"                "Navigate"            │
 │                                                                         │
 │   Headings become          Parent-child           LLM reasons about     │
 │   structural nodes         relationships          which branch to       │
 │                            from levels            explore               │
 │                                                                         │
 │   # = Root                 # (Level 1)            "For 'Widget A color' │
 │   ## = Branch              └── ## (Level 2)        I should look at     │
 │   ### = Leaf                   └── ### (Level 3)   the Products →       │
 │                                                    Widget A branch"     │
 │                                                                         │
 └─────────────────────────────────────────────────────────────────────────┘
```

---

*Created: 2026-01-27 | PageIndex v1.0*
