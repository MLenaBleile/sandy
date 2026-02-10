# Human Ratings Research Documentation

## Overview

The REUBEN dashboard includes a human rating system designed to validate and calibrate Reuben's self-assessment of sandwich quality. This document describes the research methodology, data collection procedures, and how to access the rating data for analysis.

## Research Questions

1. **Calibration**: How well does Reuben's self-assessment correlate with human consensus?
2. **Bias Detection**: Which dimensions show systematic over/under-scoring?
3. **Validation**: Do the sandwich criteria align with human intuition about structural knowledge?
4. **Edge Cases**: What types of sandwiches generate the most disagreement?

## Rating Methodology

### Rating Dimensions

Each sandwich is rated on 5 dimensions (0.0-1.0 scale):

| Dimension | Description | Interpretation |
|-----------|-------------|----------------|
| **Bread Compatibility** | Do the two bounds relate naturally to each other? | High: Bounds are semantically related (e.g., prior/posterior in Bayesian inference) |
| **Containment** | Is the filling truly contained/bounded by the bread? | High: Filling cannot exist independently of bounds |
| **Non-triviality** | Is this insight meaningful vs. trivial? | High: Non-obvious structural relationship |
| **Novelty** | Is this a fresh perspective on the concept? | High: Unique framing or unexpected connection |
| **Overall Validity** | Is this actually a sandwich structure? | High: Strong sandwich, would cite in a paper |

### Rating Scale Guidelines

- **0.9-1.0**: Exceptional - textbook example of the dimension
- **0.7-0.9**: Strong - clearly satisfies the criterion
- **0.5-0.7**: Moderate - arguable but defensible
- **0.3-0.5**: Weak - barely qualifies
- **0.0-0.3**: Fails - does not satisfy the criterion

## Data Collection

### Privacy & Anonymity

- **No PII collected**: No names, emails, or personal information
- **Session IDs**: Browser-based UUIDs stored in Streamlit session state
- **IP Hashing**: Optional SHA256-hashed IPs for spam prevention (not reversible)
- **User Agent**: Optional for detecting bots/scrapers

### Spam Prevention

| Mechanism | Purpose | Threshold |
|-----------|---------|-----------|
| **Rate Limiting** | Prevent rapid-fire submissions | 10 ratings per hour per session |
| **Duplicate Prevention** | One rating per sandwich per session | Database unique constraint |
| **IP Hash Tracking** | Detect coordinated attacks | Optional, not currently used |

### Data Quality

Ratings are included in consensus analysis only when:
1. Sandwich has ≥3 human ratings
2. Ratings are from distinct sessions
3. No obvious spam patterns detected

## Database Schema

```sql
CREATE TABLE human_ratings (
    rating_id UUID PRIMARY KEY,
    sandwich_id UUID NOT NULL REFERENCES sandwiches(sandwich_id),
    session_id UUID NOT NULL,

    -- Component scores
    bread_compat_score FLOAT NOT NULL CHECK (bread_compat_score BETWEEN 0 AND 1),
    containment_score FLOAT NOT NULL CHECK (containment_score BETWEEN 0 AND 1),
    nontrivial_score FLOAT NOT NULL CHECK (nontrivial_score BETWEEN 0 AND 1),
    novelty_score FLOAT NOT NULL CHECK (novelty_score BETWEEN 0 AND 1),
    overall_validity FLOAT NOT NULL CHECK (overall_validity BETWEEN 0 AND 1),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    user_agent TEXT,
    ip_hash TEXT,

    -- Prevent duplicates
    CONSTRAINT unique_session_sandwich UNIQUE (session_id, sandwich_id)
);
```

## Accessing Rating Data

### Via Database Query

```sql
-- Get consensus statistics for all sandwiches
SELECT
    s.sandwich_id,
    s.name,
    s.validity_score as reuben_score,
    COUNT(hr.rating_id) as rating_count,
    AVG(hr.overall_validity) as human_avg,
    STDDEV(hr.overall_validity) as human_std,
    ABS(s.validity_score - AVG(hr.overall_validity)) as disagreement
FROM sandwiches s
JOIN human_ratings hr ON s.sandwich_id = hr.sandwich_id
GROUP BY s.sandwich_id, s.name, s.validity_score
HAVING COUNT(hr.rating_id) >= 3
ORDER BY disagreement DESC;
```

### Via Dashboard API

The dashboard queries module provides helper functions:

```python
from dashboard.utils.queries import (
    get_rating_stats,                    # Overall statistics
    get_reuben_vs_human_comparison,       # Scatter plot data
    get_most_controversial_sandwiches,    # Biggest disagreements
    get_component_comparison              # Component-level analysis
)
```

### Via CSV Export

The Human Ratings Analytics page includes export functionality for:
- Full rating dataset
- Consensus statistics
- Component score comparisons

## Statistical Analysis

### Correlation Analysis

Pearson correlation coefficient measures linear agreement between Reuben and humans:

- **r > 0.7**: Strong agreement - Reuben's criteria align with human intuition
- **r = 0.4-0.7**: Moderate agreement - Systematic differences exist
- **r < 0.4**: Weak agreement - Reuben may need recalibration

### Disagreement Analysis

Sandwiches with high |Reuben - Human| scores warrant manual review:

1. **Reuben > Human**: Possible false positives (overly generous self-assessment)
2. **Human > Reuben**: Possible false negatives (overly harsh self-assessment)
3. **High variance**: Controversial sandwich (humans disagree with each other)

### Component-Level Comparison

Comparing component scores identifies which dimensions need calibration:

```python
# Example: Bread Compatibility Analysis
reuben_bread_avg = sandwiches['bread_compat_score'].mean()
human_bread_avg = ratings['bread_compat_score'].mean()

if abs(reuben_bread_avg - human_bread_avg) > 0.15:
    print(f"Bread compatibility bias detected: {reuben_bread_avg - human_bread_avg:+.2f}")
```

## Calibration Methodology

### Weight Adjustment

Reuben's validation score is a weighted sum:

```python
validity_score = (
    w1 * bread_compat_score +
    w2 * containment_score +
    w3 * nontrivial_score +
    w4 * novelty_score
) / (w1 + w2 + w3 + w4)
```

Optimize weights to minimize disagreement with human consensus:

```python
from scipy.optimize import minimize

def loss_function(weights):
    w1, w2, w3, w4 = weights
    predicted = (w1*bread + w2*contain + w3*nontrivial + w4*novelty) / sum(weights)
    return ((predicted - human_avg) ** 2).sum()

result = minimize(loss_function, [0.25, 0.25, 0.25, 0.25], method='SLSQP')
optimal_weights = result.x
```

### Bias Correction

If systematic bias is detected (e.g., Reuben consistently scores 0.1 higher), apply correction:

```python
reuben_calibrated = reuben_raw_score - bias_estimate
```

## Visualization

The Human Ratings Analytics page provides:

1. **Scatter Plot**: Reuben vs Human with perfect agreement diagonal
2. **Correlation Heatmap**: Component score relationships
3. **Box Plots**: Validity distributions by structural type
4. **Disagreement Rankings**: Top controversial sandwiches

## Citation

If you use this rating data in research, please cite:

```bibtex
@software{reuben2025,
  author = {[Your Name]},
  title = {REUBEN: Human Rating Dataset for Structured Knowledge Validation},
  year = {2025},
  url = {https://github.com/[username]/reuben}
}
```

## Contact

For questions about the rating methodology or data access:
- Open an issue on GitHub
- Review the code in `dashboard/utils/ratings.py`
- Check the Analytics page at https://reuben.streamlit.app

## Future Work

Potential extensions:

1. **Inter-rater Reliability**: Calculate Krippendorff's alpha or Fleiss' kappa
2. **Active Learning**: Prioritize which sandwiches to solicit ratings for
3. **Demographic Stratification**: Optional domain expertise tracking
4. **Temporal Stability**: Track if human ratings change as more sandwiches accumulate
5. **Adversarial Examples**: Identify sandwiches that fool Reuben but not humans

---

**Version**: 1.0
**Last Updated**: February 2025
**Status**: Active data collection
