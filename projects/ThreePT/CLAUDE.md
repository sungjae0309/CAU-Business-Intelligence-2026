# ThreePT project context

This folder is Team ThreePT's project for the Business Intelligence course (Chung-Ang University, Fall 2026).
Read these first:

1. `docs/project_plan.md` – our proposal decisions (problem, data, method, evaluation, schedule, roles) and status log
2. `docs/project_requirements.md` – what the professor requires for the project and the GitHub submission
3. `course_materials/course_notes.md` – key ideas from the Week 9–10 lectures and how they apply to this project
   (the original lecture slides and the Week 12 guideline slides/transcript are in `course_materials/`)

`course_materials/` is local only and ignored by git: lecture materials must not be published in this public repository.

## Rules

- This folder lives inside the professor's shared repository. Change files ONLY inside `projects/ThreePT/`.
- The repository is public. Never commit data files, API tokens, passwords, or personal information.
  Data stays in `data/` (ignored by git); the NYC app token is read from the `NYC_APP_TOKEN` environment variable.
- Keep `docs/project_plan.md` up to date when a decision changes, and add a line to its status log.
- Final submission: a Pull Request to the original repository titled `[ThreePT] Project Deliverables`.

## Layout

- `src/config.py` – period, complaint types, columns
- `src/collect.py` – download NYC 311 data month by month (resumes if stopped)
- `src/clean.py` – merge, clean, write `data/processed/requests.parquet` and `docs/data_summary.md`
- `src/build_dataset.py` – label, features, time split → `data/processed/dataset.parquet` and `docs/dataset_summary.md`
- `docs/` – project plan, requirements, data spec, data summary, dataset summary, proposal slides
- `course_materials/` – lecture slides, guideline slides, transcript, course notes (local only, never commit)
- `notebooks/` – analysis and modeling

## Working style

- The team lead (이성재) usually writes in Korean. Answer in Korean.
- Explain briefly what you changed and what the next step is.
