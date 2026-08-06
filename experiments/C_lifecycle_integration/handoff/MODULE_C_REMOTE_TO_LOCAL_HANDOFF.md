# Module C — Remote-to-Local Development Handoff

## Remote status at handoff

Completed on the remote GB10 repository:

- C0 repository and evidence inventory;
- C1 canonical lifecycle-stage schema;
- C2 draft cross-module evidence registry;
- C2.1 focused source-discovery audit;
- C2.3 two-layer GRI architecture;
- C2.4 worked-scenario and validation protocol.

## Important incomplete item

C2 authoritative source locking remains incomplete.

This is intentional and explicitly documented.

No final GRI formula or scored Handoff Vector engine has been created.

## Local development environment

Continue development from a WSL2 Ubuntu clone of the GitHub repository.

The GB10 GPU is not required for routine Module C work.

Likely local dependencies include:

- Python 3;
- pandas;
- numpy;
- matplotlib;
- networkx;
- jsonschema;
- pyyaml;
- scipy.

Do not reuse the A2 POD5 environment as the default Module C environment.

Create a small C-specific virtual environment locally.

## Server retention

Keep the remote repository and large A-module datasets intact until the final
paper and Module C validation are complete.

The server may still be needed to:

- locate missing A1 evidence;
- regenerate compact results from original logs;
- verify an A2 or A3 claim against retained data.

Routine Module C work should proceed locally.

## First local tasks

1. Clone or pull the main branch.
2. Verify C0 through C2.4 files are present.
3. Create a C-specific virtual environment.
4. Resolve A1 authoritative sources.
5. Regenerate compact B2 result tables.
6. Regenerate compact B3 result tables.
7. Patch and lock the C2 evidence registry.
8. Assign evidence tiers per evidence-registry row.
9. Only then implement C3 and C4.
