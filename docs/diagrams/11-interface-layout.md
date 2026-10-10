# Interface layout

The wireframe of the local Gradio demo from top to bottom, with the limitations text directly above the output and the right-to-left fields marked; it illustrates `09-ui-spec.md` §5.1.

```mermaid
flowchart TB
    subgraph TOP["header"]
        HDR["title: mini-arabic-gpt<br/>English description<br/>one-line Arabic description (right-to-left)"]
    end
    subgraph INPUT["input"]
        PROMPT["Prompt (right-to-left, 3 lines)<br/>up to 100 tokens"]
        EXAMPLES["Examples: six prompts"]
        SETTINGS["Temperature 0.1 to 1.5<br/>Top-k 1 to 100<br/>Max new tokens 10 to 200<br/>Seed (empty = random)"]
    end
    subgraph BUTTONS["actions"]
        GEN["Generate"]
        STOP["Stop"]
    end
    subgraph LIMITS["always visible, directly above the output"]
        LEN["LIMITATIONS (English)"]
        LAR["LIMITATIONS (Arabic, right-to-left)"]
    end
    subgraph OUTPUT["output"]
        CONT["Continuation (right-to-left, streams, copy button)"]
        STATUS["status: tokens, tokens/s, device, seed"]
        NORM["Prompt after normalization (right-to-left)"]
        TOKP["Prompt tokens: #, piece, id"]
        TOKC["Continuation tokens: #, piece, id"]
    end

    HDR --> PROMPT
    PROMPT --- EXAMPLES
    PROMPT --- SETTINGS
    PROMPT --> GEN
    GEN --- STOP
    GEN --> LEN
    LEN --> LAR
    LAR --> CONT
    CONT --> STATUS
    STATUS --> NORM
    NORM --> TOKP
    NORM --> TOKC
```

<!-- Sources: 09-ui-spec.md §5.1 (layout), §5.2 (components: slider ranges, rtl fields, six examples, Stop button, status line, two token tables), §5.3 (limitations text in English and Arabic, one file app/limitations.md, placed immediately before the output), UR4 and UR6 in §3 (100-token prompt cap; limitations directly above the output). -->

Reads with: `docs/09-ui-spec.md` §5.1 and §5.2.
