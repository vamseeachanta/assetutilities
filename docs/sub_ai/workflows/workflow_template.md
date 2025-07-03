## Introduction

A generic workflow template with tools highlighted. The tools and AI services are are layered such that they are interchangeable at each levels

### Summary



### Detailed Steps

#### Basic Engineering

- input data
- Read the data
- Analyze/Process the data
- Generate insights/outputs
- Communicate findings
- Save and share

```mermaid
graph TD;
    A[Input Data] --> B[Read Data];
    B --> C[Analyze/Process Data];
    C --> D[Generate Insights/Outputs];
    D --> E[Communicate Findings];
    E --> F[Save and Share];
    
    style A fill:#e1f5fe;
    style B fill:#f3e5f5;
    style C fill:#e8f5e9;
    style D fill:#fff3e0;
    style E fill:#c8e6c9;
    style F fill:#ffecb3;

    classDef input fill:#e1f5fe,stroke:#000,stroke-width:2px;
    classDef read fill:#f3e5f5,stroke:#000,stroke-width:2px;
    classDef analyze fill:#e8f5e9,stroke:#000,stroke-width:2px;
    classDef generate fill:#fff3e0,stroke:#000,stroke-width:2px;
    classDef communicate fill:#c8e6c9,stroke:#000,stroke-width:2px;
    classDef save fill:#ffecb3,stroke:#000,stroke-width:2px;

    class A input;
    class B read;
    class C analyze;
    class D generate;
    class E communicate;
    class F save;
```

#### Refinement Workflow

- **Goal**: To refine prompts for better AI tool performance.
- **Tools**: ChatGPT, Claude, Gemini, VS Code, GitHub Copilot, etc.
- **Best Practice**: Use a combination of AI tools to generate, refine, and improve prompts iteratively.
- A basic prompt using specific instructions to build better prompt (iterate amongst AI tools)
  - 
- A more advanced prompt that incorporates user feedback and context to improve results (fine-tune AI tools)
- A comprehensive prompt that combines multiple sources of information and advanced techniques for optimal results (leverage AI tools)

```mermaid
graph TD;
    A[User Input] --> B[AI Tool 1];
    B --> C[AI Tool 2];
    C --> D[Final Output];  
    style A fill:#e1f5fe;
    style B fill:#f3e5f5;
    style C fill:#e8f5e9;
    style D fill:#fff3e0;
    classDef user fill:#e1f5fe,stroke:#000,stroke-width:2px;
    classDef ai fill:#f3e5f5,stroke:#000,stroke-width:2px;
    classDef output fill:#fff3e0,stroke:#000,stroke-width:2px;
    class A user;
    class B ai;
    class C ai;
    class D output;
```

