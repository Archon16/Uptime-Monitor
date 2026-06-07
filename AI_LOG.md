# AI Collaboration Log

## AI Tech Stack

- **Tool:** Kimchi (AI Coding Agent) & GPT-5.5 (Planning) & Antigravity (IDE)
- **Model:** kimi-k2.6 (Coding) & nemotron-3-super-fp4 (Planning) & Opus 4.6 (Summarization)

## Exact AI Workflow adopted for the Project

**Phase 0**: Understanding the requirements and assessing the suitable tech stack and completion process for the project 

**Project Planning**: Using GPT-5.5 (Planning) drafted the design docs (PRD, HLD, LLD, Tech Stack). Below are the prompts in this phase:

    Prompt: "Task is to build a simple uptime monitor: a lightweight, full-stack application that periodically pings a list of URLs and displays whether each one is active, along with its response time. 

    Preferred Approach:

    I want to proceed in an orderly fashion of generating PRD, Design Doc and Tech Stack doc following with a ToDo markdown file for my AI to start coding.

    Preferred Tech Stack:

    FastAPI and python runtime for coding environment and kimchi.dev as terminal assisted AI for coding and debugging

    Act as a senior devops engineer and help me do this assignment in a organised manner as described above by generating the MVP requirements file and LLD / HLD to final code deployment"

**Building prompt:** Once the project design was ready and reviewed generated the Todo file via GPT 5.5 and fed the master prompt in kimchi dev terminal to start with projects creation. 

    Prompt: "Build the uptime monitor MVP according to the Todo file in phases. Refer to Kimchi master prompt file for instructions on how to proceed with development"

**Overview**: Once the project was completed and tested via `docker compose up` and verified that the project was working as expected, asked Antigravity's AI model (Opus 4.6) to generate the final documentation based on project architecture.

## Course Corrections

While the project was being created by Kimchi's model, there were few issues caught internally by the agent during verification phase and fixed proactively by the agent. Below are the issues and fixes:

### Issue: Database model timestamps
The initial model draft used `server_default=func.now()` with `onupdate=func.now()` for `last_checked_at`, which would have caused the database to auto-update `last_checked_at` on every SQL update rather than letting the scheduler control it explicitly. Corrected by removing `onupdate` and setting the timestamp in the scheduler code.

### Issue: Scheduler async compatibility
Initial thought was to use `AsyncIOScheduler` directly in the module, but need to ensure scheduler starts after event loop is running. Corrected by using `@asynccontextmanager` lifespan in FastAPI main.py for clean startup/shutdown.
