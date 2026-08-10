# Module C Authoritative Rebuild Notice

The current authoritative Module C results are located at:

`experiments/C_lifecycle_integration/authoritative_rebuild/`

Earlier Module C evidence-registry, GRI, findings, validation and publication artifacts are
retained for historical provenance but may contain numerical or semantic states that were
superseded after the final Module B audit.

Do not use an older Module C numerical artifact as current project evidence without checking
it against the authoritative rebuild.

The authoritative rebuild:

- locks final A/B upstream sources;
- uses the validated S1-S10 lifecycle architecture;
- rebuilds C2-C5 without consuming old Module C numerical outputs;
- regenerates C6-C8 publication artifacts;
- validates against stale superseded B3 values.

Current validated results include:

- F11 Base GRI = 1.0000000000
- Privacy Base GRI = 0.9373875000
- Privacy provenance-balanced sensitivity = 0.9242583333
- B3 authentication threshold = 3.6
- B3 authentication F1 = 0.8387

See `authoritative_rebuild/README.md` for methodology and scope.
