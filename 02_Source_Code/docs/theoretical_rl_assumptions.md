# Theoretical RL Formulations Under Explicit Assumptions

The real CynLr runtime is only partially identified from the available interface and experiments. This document therefore keeps the theoretical models separate from the empirical findings.

The rule used throughout is:

> **State the assumption first, then derive the problem class and the algorithmic consequence.**

## 1. Common assumptions

- Blue and Green positions are integer coordinates.
- `P(x,y)` supplies an absolute Blue coordinate.
- The action is therefore a finite discrete coordinate pair if the workspace is finite.
- For the theoretical abstraction, Green's next movement direction is one of the four cardinal directions:
  `(1,0), (-1,0), (0,1), (0,-1)`.
- The four-direction assumption does **not** imply that the next direction is predictable.
- Object Speed and Object Size are held fixed during an episode.
- The task objective is to keep Blue within the Green Dot bounds.

These are modeling assumptions, not claims that the live application was proven to satisfy all of them.

---

## 2. Case A - Instantaneous Blue teleportation

### Assumptions

1. The streamed coordinates are true positions in a common coordinate system.
2. `P(x,y)` immediately places Blue at `(x,y)`.
3. There is no action or observation delay relevant to the decision.
4. The agent observes the current Green position before acting.

### Dynamics

`B_(t+1) = a_t`

Choosing `a_t = G_t` directly matches Blue to the currently observed Green position.

### Consequence

Under these assumptions the control problem collapses to direct feedback. There is no strong reason to introduce RL: the optimal action is available immediately from the current observation.

This is a useful sanity-check case rather than the proposed RL solution.

---

## 3. Case B - Fixed one-step delay with uncertain Green motion

### Assumptions

1. Blue still teleports to the commanded integer coordinate.
2. The command chosen at `t` takes effect at `t+1`.
3. Green moves on the integer grid.
4. Green's next direction is one of the four cardinal directions.
5. The next direction is not assumed deterministic or inferable from a short history.
6. Recent Green history is available to the agent.

### Dynamics

`B_(t+1) = a_t`

`G_(t+1) = G_t + Delta_(t+1)`

with Delta in the four-direction set.

### Candidate state

`S_t = (G_t, B_t, G_(t-1))`

The previous Green position exposes recent motion, but whether one previous step is sufficient for a Markov state is itself an assumption that would require empirical validation.

### Action

`A_t = (x_cmd, y_cmd)`

where both coordinates are legal integers.

### Reward

A dense theoretical surrogate is:

`r_(t+1) = - ||G_(t+1) - B_(t+1)||_2`

The actual application objective is the inside/outside Green-bound condition. That criterion should be used as the primary task measure once its timing and geometric definition are established.

### Problem class

This is a finite discrete-action MDP only if the chosen state contains all information needed for the transition distribution. Under that explicit assumption, a value-based method such as DQN is a reasonable theoretical candidate.

However, because Green can be action-independent, the problem may behave more like a contextual prediction/decision problem than a strongly coupled long-horizon control problem. This should be recognized before implementing an RL agent.

---

## 4. Case C - Hidden or variable command delay

### Assumptions

1. `P(x,y)` affects Blue, but the effective delay is hidden or variable.
2. Observation records arrive asynchronously relative to commands.
3. The agent cannot observe the internal command-processing state.

### Hidden state

The true state could include variables such as command-in-flight status or remaining processing delay.

### Consequence

Two identical visible observations may correspond to different hidden situations. The visible process may therefore be non-Markov.

A history-augmented state or recurrent memory can be used to retain information about recent commands and observations.

This case is the most natural theoretical explanation for why the real application cannot safely be reduced to a simple one-observation/one-action MDP without first establishing timing semantics.

---

## 5. Case D - Stochastic Green motion as a standard MDP

This is a narrower mathematical model, not a claim about the application's implementation.

Assume Green's movement is Markov given the current state:

`P(Delta_t | S_t)`

where `Delta_t` belongs to the four-direction set.

Then a finite-grid state such as `(G_t, B_t)` can be sufficient **if that Markov assumption is explicitly adopted**.

The resulting problem is a finite-state, finite-action MDP and Q-learning/DQN becomes a natural family to study.

The important distinction is that the Markov assumption is added explicitly. Four possible directions alone do not establish Markovity or predictability.

---

## 6. Counterfactual: known future Green path

If the full future Green path and the effective command delay were known, the future target could be calculated directly and model-based control could be used. This is a counterfactual boundary case, not an assumption of the task.

In particular, I do not assume that recent history is enough to predict the testing path.

---

## 7. Recommended theoretical formulation

For a concrete RL study, I would use a deliberately modest model:

### Assumptions

- integer coordinate grid;
- Blue teleportation;
- fixed one-step command delay as a modeling simplification;
- Green moves one grid step per decision interval;
- next Green direction belongs to the four cardinal directions but is uncertain;
- recent Green history is available;
- one previous Green position is tentatively included in the state;
- the process is treated as Markov only as an explicit modeling assumption;
- Object Speed and Object Size are fixed per episode.

### State

`S_t = (G_t, B_t, G_(t-1))`

### Action

`A_t = (x_cmd, y_cmd)` with legal integer coordinates.

### Transition

`B_(t+1) = A_t`

`G_(t+1) = G_t + Delta_(t+1)`

### Reward

Dense surrogate:

`r_(t+1) = - ||G_(t+1) - B_(t+1)||_2`

Task criterion:

`+1` when Blue is within the Green bounds, otherwise `0`, once the geometry/timing is verified.

### Algorithmic direction

Because the action is a discrete coordinate pair, a value-based approach such as DQN is a theoretical starting point. The large coordinate-pair action set is an action representation problem; it does not turn the action space into a continuous one.

If hidden delay remains important, a history-aware or recurrent value-based model is the more faithful extension.

---

## 8. What would need to be established before empirical RL

Before training on the real application, I would still need:

- a reliable command-to-observation timing convention;
- practical legal coordinate bounds;
- a defined decision interval or explicit variable-delay model;
- a verified reward/measurement clock;
- an episode reset/end convention;
- evidence that the chosen state is sufficiently Markov, or an explicit memory mechanism.

Until then, the formulations in this document remain theoretical.
