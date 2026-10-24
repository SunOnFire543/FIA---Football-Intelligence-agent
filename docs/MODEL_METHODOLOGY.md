# Statistical Modeling Methodology

## 1. Match Outcome Model: Bivariate Dixon-Coles Goal Model

### 1.1 Goal Distribution Formulation
Match goals for home team $X$ and away team $Y$ are modeled using independent Poisson baselines modified by the Dixon-Coles adjustment parameter $\tau_{\lambda, \mu}(x, y)$ to account for low-score dependence (especially 0-0, 1-0, 0-1, 1-1):

$$P(X = x, Y = y) = \tau_{\lambda, \mu}(x, y) \cdot \frac{\lambda^x e^{-\lambda}}{x!} \cdot \frac{\mu^y e^{-\mu}}{y!}$$

Where the adjustment factor $\tau$ is defined as:
$$\tau_{\lambda, \mu}(x, y) = \begin{cases}
1 - \lambda \mu \rho & \text{if } x = 0, y = 0 \\
1 + \lambda \rho & \text{if } x = 0, y = 1 \\
1 + \mu \rho & \text{if } x = 1, y = 0 \\
1 - \rho & \text{if } x = 1, y = 1 \\
1.0 & \text{otherwise}
\end{cases}$$

Here $\rho \approx -0.08$ reflects the observed negative correlation in low scores in top-flight European football.

### 1.2 Expected Goals Estimation ($\lambda, \mu$)
Expected goals are estimated from historical match logs:
$$\lambda_{\text{home}} = \alpha_{\text{home}} \cdot \beta_{\text{away}} \cdot \gamma_{\text{home\_adv}} \cdot \bar{G}$$
$$\mu_{\text{away}} = \alpha_{\text{away}} \cdot \beta_{\text{home}} \cdot \bar{G}$$

Where $\alpha$ is team attack strength, $\beta$ is defensive fragility, $\gamma_{\text{home\_adv}} \approx 1.22$ is the home advantage multiplier, and $\bar{G}$ is league average goals per game.

### 1.3 Derived Market Probabilities
Over the truncated joint matrix $S(x, y)$ for $x, y \in [0, 7]$:
- **Home Win**: $P(1) = \sum_{x > y} S(x, y)$
- **Draw**: $P(X) = \sum_{x = y} S(x, y)$
- **Away Win**: $P(2) = \sum_{x < y} S(x, y)$
- **Double Chance**: $P(1X) = P(1) + P(X)$, $P(12) = P(1) + P(2)$, $P(X2) = P(X) + P(2)$
- **Over/Under $T$ Goals**: $P(\text{Over } T) = \sum_{x+y > T} S(x, y)$, $P(\text{Under } T) = 1 - P(\text{Over } T)$
- **Both Teams To Score (BTTS)**: $P(\text{BTTS Yes}) = \sum_{x \ge 1, y \ge 1} S(x, y)$

---

## 2. Player Prop Proposition Modeling
Player markets (Shots, Shots on Target, Anytime Goalscorer) use per-90 event rates scaled by expected playing minutes and starting status:
$$\lambda_{\text{player}} = \text{Rate}_{\text{per } 90} \cdot \left(\frac{\text{Expected Minutes}}{90}\right) \cdot \delta_{\text{opp\_def}}$$

Poisson cumulative distributions then estimate probabilities for:
- Over $0.5, 1.5$ Shots on Target (SOT)
- Over $1.5, 2.5$ Total Shots
- Anytime Goalscorer: $P(\text{Goal}) = 1 - e^{-\lambda_{\text{goals}}}$

---

## 3. Parlay Dependency & Joint Probability Modeling
For same-match combinations (e.g. Arsenal Win and Over 1.5 Goals):
$$P(\text{Home Win} \land \text{Over } 1.5) = \sum_{x > y \land x+y > 1.5} S(x, y)$$
This evaluates the exact joint probability across the bivariate score matrix, completely avoiding the mathematical error of multiplying correlated individual probabilities.

For multi-match selections across independent fixtures:
$$P(\text{Joint}) = \prod_{i=1}^N P(\text{Leg}_i)$$
