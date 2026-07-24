# Analysis Pipeline

```mermaid
flowchart LR
    A["Controlled Markdown notes"] --> B["Phase 1: deterministic baseline extraction"]
    C["Controlled screenshots"] --> D["Phase 2: local OCR"]
    B --> E["Phase 3: deterministic typology coding"]
    D --> E
    E --> F["Phase 4: deterministic financial-crime analysis"]
    F --> G["Privacy-safe aggregate outputs"]
    H["Blinded independent human coding"] --> I["Frozen pre-adjudication ICR"]
    I --> J["Separate consensus adjudication"]
    J --> K["Privacy-safe aggregate validation results"]
```

## Boundary

Complete controlled inputs and record-level outputs remain outside GitHub. The public exporter permits only named aggregate files. No Phase 3b, Phase 4b, Phase 5, or LLM-assisted empirical pathway is included.
