# CynLr RL - Phase 1: Environment & Protocol Characterization

## Goal

Before choosing an RL algorithm, I treated the CynLr application as a black-box system and investigated its TCP interface and runtime response.

## What the interface establishes

The application streams Green X/Y, Blue X/Y, Error X/Y and framing bytes in a 20-byte observation record. The `P` command carries an absolute Blue X/Y coordinate. `C` is configuration for Object Speed and Object Size rather than the per-step action.

The live protocol was interpreted as **big endian**.

## Experiments completed

- passive observation stream;
- single `P` command;
- timestamped command response;
- repeated fixed position command;
- command refresh timing;
- Object Size effect;
- simple Green-following controller;
- Error metric probe.

## Findings

Established:

- TCP connection works;
- packet framing and parsing work;
- observations are continuously streamed;
- `P` affects Blue-related behaviour;
- command timing/frequency changes observed behaviour.

Not established:

- exact temporal semantics of `P`;
- causal alignment between a `P` command and an observation record;
- exact processing/response delay;
- Error X/Y semantics;
- GUI Error % as a per-step reward;
- exact coordinate bounds;
- whether the visible state is Markov.

## Decision

I stopped empirical system identification at this point because the remaining uncertainties change the RL state, transition, reward clock and action frequency themselves. I did not claim empirical RL performance on an unverified MDP.

## Theoretical follow-up

The separate document `theoretical_rl_assumptions.md` considers several explicit models: instantaneous teleportation, fixed delayed teleportation with uncertain Green motion, hidden/variable delay, and a narrower stochastic-MDP abstraction.

The four-direction Green assumption is used only to define the set of possible next directions. I do **not** assume that future Green motion is deterministic, known, or inferable from a short history.

## Phase 1 thesis

> The TCP interface is understood well enough to formulate hypotheses, but the temporal semantics of the control loop are not sufficiently identified to claim a validated RL environment. Therefore the final RL formulation is explicitly theoretical.
