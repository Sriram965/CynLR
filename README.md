# CynLr - Machine Learning / RL Assignment

This repository contains my work on the CynLr **Chasing the Dot** problem.

The task is to control a Blue Dot while a Green Dot follows a path. I approached it in two stages: first I tried to understand the real application and its interface; then I identified the assumptions under which an RL model could be defined without claiming that those assumptions were established by the runtime.

## What I implemented

The application communicates over TCP. I implemented the 20-byte observation parser, the 13-byte `P` position command, the 17-byte `C` configuration command, and a TCP client that reads complete observation records and sends commands.

The live protocol was interpreted as **big endian**.

Core code:

```text
src/protocol.py
src/cynlr_client.py
```

## Why I investigated the environment first

The manual gives the packet structure and the purpose of the `P` command, but it does not fully specify the timing semantics of the control loop. I therefore treated the application as a black box before choosing an RL algorithm.

The experiments covered:

- passive observation streaming;
- a single `P` command;
- timestamped response after a command;
- repeated position commands;
- command refresh frequency;
- Object Size configuration;
- a simple Green-following controller;
- whether the GUI Error % and Error X/Y fields form a usable per-step learning signal.

The scripts and recorded outputs are in `experiments/` and `results/`.

## What I established

The TCP connection works and the observation/command framing can be handled consistently. The application continuously emits observations, so reading the next 20-byte record after a `P` command does not automatically give a causal response to that command.

A `P` command affects Blue-related behaviour, and changing the command timing/frequency changes what is observed. The simple Green-following controller also gave qualitative evidence that timing matters: tracking was easier when Green moved more slowly and became more variable when Green moved faster.

## What I could not establish

I could not reliably determine:

- whether `P(X,Y)` is an instantaneous placement, an internal target, a delayed action, or another mechanism;
- the exact action-to-observation delay and command queue/overwrite behaviour;
- the causal correspondence between a particular `P` and a particular streamed observation;
- the meaning of the raw `Error X` and `Error Y` fields;
- whether the GUI Error % is a suitable per-step learning signal;
- the exact legal coordinate bounds;
- whether the visible observation is Markov without adding history.

Because these points determine the RL environment itself, I did not claim a trained RL agent on the real runtime.

## Assumption cases for a possible RL model

I considered a small set of explicit environment assumptions rather than assuming one hidden runtime model:

### Case A - Instantaneous teleportation

If `P(X,Y)` immediately places Blue at the supplied coordinate and the current Green position is observed before acting, direct feedback control may be sufficient and RL may not be necessary.

### Case B - Fixed one-step delay

If a command takes effect one step later, while Green moves on an integer grid with one of the four cardinal directions, the problem can be treated as a discrete decision process under an additional Markov assumption. The direction is **not** assumed to be predictable.

### Case C - Hidden or variable delay

If the effective command delay or internal command-processing state is hidden or variable, the visible observation may not be Markov. A history-aware or memory-based model may then be needed.

These cases are assumptions, not measured descriptions of the final runtime dynamics. The detailed theoretical treatment is in:

```text
docs/theoretical_rl_assumptions.md
```

## What I do not assume

I do **not** assume that Green's future direction is deterministic, that a short history always predicts the future path, that the testing trajectory is known in advance, or that the four-direction movement rule by itself makes the process Markov.

The four-direction rule defines the set of possible next directions; it does not establish which direction will occur.

## Why the action space is discrete

The command supplies integer coordinates. If the legal workspace is

```text
x = 0, ..., W
y = 0, ..., H
```

then the coordinate-pair action set is finite:

```text
|A| = (W+1)(H+1)
```

It can be very large, but it is still a discrete action space. The detailed implications for a possible RL model are kept in the theoretical assumptions document rather than presented as an empirical result.

## Final scope

The empirical part of this repository records what I could establish from the live application. The assumptions document records how the problem class could change under different runtime semantics. A concrete RL model can be built once the remaining timing, geometry, and state/reward semantics are established; I do not present one as a validated model of the current runtime.
