# Example Case Studies

An approximation of the current AI workflows is illustrated by the following case studies. These examples show how users interact with AI tools to generate, refine, and improve code or workflows across different domains.

### Summary

Identify a good practice. Need not be the best practice, but a good practice that is being used by the community.
- **Solution**: Use a combination of AI tools and IDEs to generate, refine, and improve code.
- **Tools**: ChatGPT, Claude, Gemini, VS Code, GitHub Copilot, etc.
- **Best Practice**: Encourage collaboration between AI tools and human developers to leverage the strengths of both.

Mermaid flowchart TBA

### Case study : Electrical SME Engineering

ChatGPT chat and get results

```mermaid
flowchart LR
    A[User] --> B[ChatGPT]
    A --> C[Generated Code]
    C --> D[Refined Code]
    D --> E[Further Refinement]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#fff3e0
    style D fill:#e8f5e8
    style E fill:#e8f5e8
```


### Case study : Mechanical SME, Engineering

Mainly work in text based files such as markdown, yaml, python code, mermaid charts using below tools:
- VS code
- GitHub Copilot Inline chat
- Claude Sonnet 4

```mermaid
flowchart LR
    A[User] --> B[VS Code]
    A --> C[GitHub Copilot Inline Chat]
    A --> D[Claude Sonnet 4]
    B --> E[Generated Code]
    C --> F[Refined Code]
    D --> G[Further Refinement]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#fff3e0
    style D fill:#e8f5e8
    style E fill:#e8f5e8
    style F fill:#e8f5e8
    style G fill:#e8f5e8
```




### Case study : Transportation SME Engineering

    I have been using the free Google AI Studio for the past few months....I really like it. I sometimes play the LLMs with each other. Give Google's Code to ChatGPT and ask it to refine further and vice-versa.

```mermaid
graph LR
    A[User] --> B[Google AI Studio]
    A --> C[ChatGPT]
    B --> D[Generated Code]
    D --> C
    C --> E[Refined Code]
    E --> B
    B --> F[Further Refinement]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#fff3e0
    style D fill:#e8f5e8
    style E fill:#e8f5e8
    style F fill:#e8f5e8
```

### Case study : AI First Workflows, Product Development, Every

    These days it's Claude code inside vs code for me. Looks like that's the way things are evolving, with Gemini cli released a couple of days ago

```mermaid
flowchart LR
    A[User] --> B[Claude Code]
    A --> C[VS Code]
    B --> D[Generated Code]
    D --> C
    C --> E[Refined Code]
    E --> B
    B --> F[Further Refinement]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#fff3e0
    style D fill:#e8f5e8
    style E fill:#e8f5e8
    style F fill:#e8f5e8
```


### Case study : AI First Workflows, Company (Vora)

User Prepares a mental model for AI to do the following with user approval at every step:
- Prepare a Github Issue
- Prepare Code to implement the issue
- Write tests
- Write documentation
- Create a PR
- Run a test suite

```mermaid
flowchart TD
    A[User Mental Model] --> B[Prepare GitHub Issue]
    B --> C{User Approval}
    C -->|Yes| D[Prepare Code Implementation]
    C -->|No| B
    D --> E{User Approval}
    E -->|Yes| F[Write Tests]
    E -->|No| D
    F --> G{User Approval}
    G -->|Yes| H[Write Documentation]
    G -->|No| F
    H --> I{User Approval}
    I -->|Yes| J[Create Pull Request]
    I -->|No| H
    J --> K{User Approval}
    K -->|Yes| L[Run Test Suite]
    K -->|No| J
    L --> M[Complete Workflow]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style D fill:#fff3e0
    style F fill:#e8f5e8
    style H fill:#e8f5e8
    style J fill:#e8f5e8
    style L fill:#e8f5e8
    style M fill:#c8e6c9
```

References

https://youtu.be/Lh_X32t9_po?si=CV3DXT9gaPTH8_xh


### Other References

TBA
