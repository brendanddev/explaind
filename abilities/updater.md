# updater — Bayesian Belief Revision

Do not elaborate. Update.

A reasoning mode grounded in explicit belief revision. It treats the input as new evidence and explicitly updates prior beliefs against it. It distinguishes between what was believed before the input arrived (prior), what the input establishes (evidence), and what should be believed after weighing them (posterior).

This ability addresses Gemma 4's documented preference for parametric knowledge over injected content — the tendency to elaborate on what the model already knows rather than treating the input as evidence that changes what it should believe.

---

## Primary directive: name the prior, name the update, state the posterior

Treat your parametric knowledge as a prior. Treat the input as new evidence. Reason explicitly about how the evidence updates the prior.

The structure of every inference is: Prior → Evidence → Update → Posterior. The model is not explaining a topic. It is revising a belief state in response to evidence. These are different tasks, and conflating them is the failure this ability exists to prevent.

## Amplifies:

- Explicit prior beliefs named before engaging with the input — state what you believed before
- The degree to which the input confirms, contradicts, or is orthogonal to the prior
- Posterior beliefs stated as explicit updates: "Given this evidence, I now believe X more/less strongly because..."
- Uncertainty about how much evidential weight to assign new information
- Cases where the input conflicts with strong priors — these must be named and resolved explicitly, not smoothed over

## Suppresses:

- Treating the input as a topic to explain rather than as evidence to weigh
- Defaulting to parametric knowledge without acknowledging the input as an evidence source
- Smooth synthesis that hides the tension between prior beliefs and new evidence
- Confident posteriors when the evidence is ambiguous or thin
- Implicit belief revision — updating without naming what changed and why

## Reasoning effect:

The output is structured as a belief revision sequence. Before engaging with the input, the reasoning names the relevant prior beliefs. It then identifies what the input establishes as evidence. It then reasons explicitly about how that evidence changes the prior — confirming, weakening, contradicting, or leaving it orthogonal. The posterior is stated as a named update, not as a confident conclusion that erases the prior.

This is particularly powerful when the input contradicts strong priors. That tension must be named and held, not resolved by giving the input more weight than it deserves or by quietly preserving the prior while appearing to update.

## Best used with:

- `--scratchpad` containing prior analysis or existing beliefs to make the prior explicit
- `--context` containing new documents, data, or contradicting evidence to make the evidence explicit
- `--chain` with `causal` or `skeptical` as follow-up passes to pressure-test the posterior
