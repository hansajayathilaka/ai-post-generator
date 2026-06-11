The software industry has entered a critical phase of generative AI adoption. While the initial wave focused on training developers to use IDE assistants like GitHub Copilot, Cursor, and Claude Code, engineering organizations now face a harder problem: **What is this AI spend actually producing, and where is the ROI?**

According to Gartner, worldwide AI software spending is scaling rapidly, yet Harness’s *2026 State of Engineering Excellence* report reveals a massive measurement gap: **94% of engineering leaders** state that critical cost and productivity metrics are missing from their current frameworks ([Harness.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH5j3XWC6SEvAM816OTFFn6gJBU8bbL4VnJRWgQl30f1wUXl_UoOY4x3HgDYmJGc0FVyvVm6fONhD3SVvhfeHRf5XY_Ytfhb3l4-PR8wmRhCYU=)). 

To address this, software delivery platform Harness has launched two new products in public beta: **AI DLC Insights** and **Cloud & AI Cost Management (CACM)** ([devops.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEywDCigXLh-MTuq4OdcZvqZoKUrEPWAibFJOYjzIo5-Zb6SdpSLCG2xRqLXcSk8FGjAIPWr30eyA6SM_Rj_SNKnoHPrhK0_2Up3uEwbK3nwzTZzt01FfStvPYsmt3cfG4dTlmxpR5xed_aUg4qfS_xZNcJ6ggyc7mL3_sQMA==)). These tools address the two distinct components of enterprise AI spend: developer token consumption (the inner loop) and production inference/agentic infrastructure (the outer loop).

---

### 1. AI DLC Insights: Unifying the Inner Loop
The "AI Velocity Paradox" highlights a major bottleneck: while developers write code faster using generative tools, subsequent pipeline stages—such as security validations, CI builds, and PR reviews—often stall delivery ([computerweekly.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEHm53fX4dvP3fynF1BAw4BeUf6D8PN2xImJLGpIcnncUS6a4ad47LSy_PCwYkiWYNXQteqLR9lr28ahRgXgNgTLnXpvxbiEMeRR34gnZmW4u5a1cVIsKUIA1nAGIYcLVR16sEmU9HpHY7UhTVxLU_OoEl894c89Xxmbr-gPNgmRAhJMZqfScJGfiCZY6A42V42UCh7PiWSpY5LclGF)). Furthermore, "tokenmaxxing"—generating massive blocks of code that are ultimately rejected or heavily refactored—silently inflates development costs.

**AI DLC (AI Development Life Cycle) Insights** connects to the developer’s local machine via an **on-machine developer agent** ([Harness-engineering.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYG0JHJ62ZaLmJJX-J_Gkozowcaoi1if5OmFPbqyXPsuPKY9hf97KuULK5CUBVC2sdBXowX02JMPXuLajr_ZBcb2JCk7UfqFdoN9DlCmVekMyN7oBmbHs6flUnuD65nuWRfU34Ctpdjpu-OCLH30XKvkbNDe3tdi4ihnqntSM2fOAETWJtle7RLpZTB16hswI-3bNzNV6eedktHvsukrCp0=)). This daemon captures:
* Real-time IDE telemetry (VS Code and Cursor IDE integrations).
* Terminal-based prompt activity (e.g., Claude Code, CLI assistants).
* Staging Git diffs.

By mapping local telemetry to the **Harness Software Delivery Knowledge Graph**, the tool matches LLM token costs directly to specific Jira tickets, PRs, and DORA metrics ([Harness.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQG07DTCcveKZjCv62QKvab0xDpx4WxZgj9JiSth96zpAOL7nt7FaQA8KCGaCXKNmL2-RlymmjFleNMO-_7A2ntdV3GYNbEacWILI74zwNULCmO-rdqXZT1KWhAPmfMfu1Rog38ehTXPV_hRWr_gS_VfFlW59g0YwEZwXr1HB7Y2subvo9jFcRJTbakm5LlO_Koui29ez57nPLWWZEgo6IM=)). Teams can trace precisely how much AI-generated code actually ships versus how much is discarded, quantifying the exact cost-to-outcome ratio.

---

### 2. Cloud & AI Cost Management: Demystifying the Outer Loop
Once applications ship, organizations struggle to break down aggregate cloud bills to identify the root cost drivers of production LLM workloads. **Cloud & AI Cost Management (CACM)** connects directly to foundational model and infrastructure providers—including **OpenAI, Anthropic, AWS Bedrock, and Google Cloud Vertex AI** ([ai-techpark.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHeeD5tS2v7t0oHXzk027NMrFQo2CDU16-zQNsNrKSFJyksYNGlSxhGElQNHXQWTjF0-93VN4VfNvEF4L9DoEKuTBQSdtfd5tKV5pRbGxFD5QOGs-2R9SRTHON3477A6ZbuVys2ZQYEzbTeYWEC8ggAHMX2EJ1ISoxKdCS5Km91Px0W1klL5p7KotswUim_)).

CACM provides deep observability into multi-agent workflows and LLM runtimes, breaking costs down dynamically:
* **Granular Attribution:** Trace consumption by specific agent runs, customer sessions, or recursive loops.
* **Proactive Guardrails:** Detect runaway loops and anomalous token spikes before they trigger massive enterprise invoices ([Harness.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFoJx-oz3vyR6VgV8PtL-_6PHyUhxyfvgSzmWg7COlk589AakNrhDXqJYqu-VF3XtqMQ7ryIpOYRCztw721idEgXtzFHfm5ybOgKwBxX7rtfcGyNa0W04EONFZNR1wwYncBslbk2pv8NnI5GSx3WlY--yh7RViE2-o1bugbYcvgAe_qpoNRoaDz9dNEh3cp5Q==)).

---

### Under the Hood: Telemetry and Lineage Tracing

```
[ IDE Prompts / CLI ] ---> [ On-Machine Agent ] ---> [ Git Commit Diffs ]
                                                             |
[ Production Deploy ] <--- [ DORA / CI/CD Pipeline ] <-------+
```

To achieve session-level granularity, the lightweight daemon running on developer workstations monitors IDE and terminal actions. When a developer makes a commit, the agent maps the local prompt telemetry deterministically to the staged Git diffs. This linkage is pushed to the Harness Software Delivery Knowledge Graph, correlating raw token spend with downstream build logs and production deployments. 

On the operations side, CACM monitors LLM API calls programmatically, using unified provider integrations to capture multi-turn conversational sequences and model parameters in real time. This allows managers to attribute inference costs directly to specific customer IDs or background microservices. Both products are now available in public beta ([prnewswire.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH7_MxJyq4wy-5bB6xRXST9ac5y-sOFXnKFvy_N8pZ5WfGRVtD7RLCy7bx6ruskjjBYlxS2cvP7o9GNUv-SAzzNaEQDF2IKH3ECdZdEL1sbFOA1aSbm7CB8TloHiRaSQTycp11LLVhsbX8vfgdaNQdbJcGrttsb9CG3lw8oXxzCSTXNQPuHs90B4w4UN7pEfz0uYetNUKW-jhEPwwH44zYtBjF-lkArjbcjzu0IBMMcpxLAKfdblqNE5nZnZmoFhuD710M5CB9mPVhWxdLa8iKVopUbAhFKBuNL)).