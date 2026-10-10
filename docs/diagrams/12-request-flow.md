# Request flow

What happens between a click on Generate and the final status and token tables: validation, normalization and encoding, the generation loop with streaming, and Stop cancelling the loop; it illustrates `09-ui-spec.md` §5.4 and §6.1.

```mermaid
sequenceDiagram
    actor U as User
    participant UI as Gradio app
    participant T as Tokenizer object
    participant G as generate loop
    participant M as Model

    U->>UI: click Generate (prompt, temperature, top-k, max new tokens, seed)
    UI->>UI: empty prompt?
    alt prompt is only whitespace
        UI-->>U: error "Please enter a prompt (a few words in Arabic)." (no generation)
    end
    UI->>T: normalize and encode the prompt
    T-->>UI: token ids
    alt more than 100 tokens
        UI-->>U: error "The prompt is N tokens#59; the limit is 100 (about 60 words). Please shorten it." (no generation)
    end
    opt device is the CPU and max new tokens is above 100
        UI-->>U: warning, outputs of more than 100 new tokens can take more than 10 seconds
    end
    UI->>G: start (seed shown, drawn at random if empty)
    loop at most max_new steps, stop at endoftext
        G->>M: current context
        M-->>G: logits
        Note over G: divide by temperature, keep the top_k largest, sample with the seeded generator, append
        opt every 4 new tokens
            G-->>UI: partial text
            UI-->>U: streamed text
        end
        opt user clicks Stop
            U->>UI: Stop
            UI->>G: cancel the running event
        end
    end
    G-->>UI: final text, status, prompt and continuation token tables
    UI-->>U: continuation, status line, normalized prompt, two token tables
```

<!-- Sources: 09-ui-spec.md §6.1 (steps 1 to 5: normalize and encode; more than 100 tokens, or none, is rejected; loop for at most max_new steps with temperature, top-k, seeded sampling, stop at <|endoftext|>; text yielded every 4 new tokens and once more at the end with the status and the two token tables; seed drawn at random once if empty and shown), §5.4 (the messages and the CPU warning above 100 new tokens), §5.2 (Stop cancels the running event), UR4 (100-token prompt cap). -->

Reads with: `docs/09-ui-spec.md` §5.4 and §6.1.
