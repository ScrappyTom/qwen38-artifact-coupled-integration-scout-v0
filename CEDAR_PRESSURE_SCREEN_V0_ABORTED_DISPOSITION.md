# Cedar pressure screen v0 — sealed apparatus abort

The authorized run
`2026-08-25-cedar-ingress-aligned-pressure-screen-v0` stopped before starting
the project model server or making any provider/actor call.

The frozen runner found a pre-existing `llama-server.exe` process (PID 17032)
using a different executable path, model package, context size, and port. It
was not launched by this repository. The no-coexistence guard rejected the run
before inference. The external process was inspected but not terminated.

The attempted run remains append-only under
`runs/2026-08-25-cedar-ingress-aligned-pressure-screen-v0/`. Its authorization,
freeze binding, runtime-asset verification, failure, finalization, and tree
seal are exact. It contains:

- provider calls: 0;
- actor calls: 0;
- project GPU server starts: 0; and
- scientific evidence: none.

The same run ID may not be retried. A mechanically identical v1 screen must use
a new run ID, a new clean frozen commit, and separate owner authorization. It
may start only when the external llama server is no longer running; this
repository will not stop an unrelated user process.
