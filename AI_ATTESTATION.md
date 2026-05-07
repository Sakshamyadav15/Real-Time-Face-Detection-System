# AI Collaboration Attestation

## Tools Used

Claude Sonnet (via Kiro IDE) was used as the primary AI assistant throughout this project. The Kiro spec-driven workflow was used to scaffold the initial directory structure and generate first-pass implementations of individual modules.

## What AI Generated

The initial boilerplate for FastAPI route handlers, SQLAlchemy model definitions, Pydantic schemas, Docker Compose configuration, and React component structure was AI-generated from a detailed specification I authored. The Alembic migration, nginx configuration, and .env.example were also generated from explicit prompts.

## What I Reviewed, Corrected, and Decided

Every generated file was read and reviewed before being accepted. The face detection fallback chain required multiple iterations — the initial MediaPipe implementation did not correctly handle the case where no face is present in the frame, returning a false positive instead of None. I identified this, diagnosed the issue, and directed the corrected implementation.

The WebSocket broadcaster's queue drop behaviour for slow clients was not in the first generated version. I identified the race condition risk, specified the asyncio.Queue maxsize approach, and verified the implementation was correct.

The annotator module was checked line by line to confirm no cv2 import appeared anywhere in the dependency chain, including transitive imports through MediaPipe. This was a hard requirement and I treated it as one.

Architectural decisions — the three-endpoint API design, the choice of PostgreSQL over a document store, the decision to keep the broadcaster as an in-process singleton rather than introducing a message broker, and the single-table schema — were made by me before any code was written. AI implemented decisions I had already made, not the other way around.

The frontend layout and component structure were redesigned manually after the initial AI-generated version did not meet my standards for usability.

## What AI Was Not Used For

Debugging integration issues between containers was done manually. The docker-compose networking configuration required hands-on iteration. The final git history was structured by me to reflect the logical build order of the system.

## Assessment

Using AI on this project was equivalent to having a fast typist who knows the syntax well but needs clear direction on architecture and edge cases. The output required consistent review and several corrections. The value was in acceleration of implementation, not in design or problem-solving.
