# Sandy Dashboard

Interactive web dashboard for monitoring and exploring Sandy's sandwich-making process.

## Features

- **📊 Live Feed**: Real-time stream of sandwich creation with auto-refresh
- **🔍 Browser**: Searchable, filterable corpus explorer
- **📈 Analytics**: Research-grade metrics and visualizations
- **🗺️ Exploration**: Network graph of sandwich relationships
- **✨ Interactive**: User-guided sandwich creation (requires full agent)
- **⚙️ Settings**: Configuration, data export, and system controls

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Docker and Docker Compose (optional but recommended)

### Option 1: Docker Compose (Recommended)

```bash
# Start database and dashboard
docker-compose up -d

# Initialize database schema
python scripts/init_db.py

# Seed with structural types
python scripts/seed_taxonomy.py

# Dashboard will be available at http://localhost:8501
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r dashboard/requirements.txt

# Set environment variable
export DATABASE_URL="postgresql://sandwich:sandwich@localhost:5432/sandwich"

# Start dashboard
streamlit run dashboard/app.py

# Open browser to http://localhost:8501
```

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (required)
  - Format: `postgresql://user:password@host:port/database`
  - Default: `postgresql://sandwich:sandwich@localhost:5432/sandwich`

### Streamlit Secrets

Alternatively, create `.streamlit/secrets.toml`:

```toml
DATABASE_URL = "postgresql://sandwich:sandwich@localhost:5432/sandwich"
```

## Usage

### Navigating the Dashboard

The sidebar provides navigation between all pages:

1. **Live Feed** - Watch sandwiches being created in real-time
   - Auto-refreshes every 2 seconds
   - Filter by validity score and structural type
   - Adjust display limit (5-100 sandwiches)

2. **Browser** - Search and filter the entire corpus
   - Full-text search across all fields
   - Filter by validity range, type, and source domain
   - Pagination for large datasets
   - Click rows to see detailed information

3. **Analytics** - View metrics and trends
   - Foraging efficiency over time
   - Validity score distribution
   - Structural type heatmap (type × source domain)
   - Component score breakdown (radar charts)
   - Export data as CSV

4. **Exploration** - Network graph visualization
   - Force-directed layout
   - Node size = validity score
   - Node color = structural type
   - Edges = similarity relationships
   - Search to highlight nodes

5. **Interactive** - Guide Sandy to make a sandwich
   - **Note**: Requires full agent (Prompts 4-10)
   - Provide topic or URL
   - Watch step-by-step process
   - Accept, reject, or edit results

6. **Settings** - Configuration and data management
   - Adjust validation weights
   - Export corpus (CSV or JSON)
   - Clear dashboard cache
   - Manage sources (coming soon)

### Creating Test Data

To populate the dashboard with test data:

```python
# scripts/seed_test_data.py (create this file)
from src.sandwich.db.repository import Repository
from src.sandwich.db.models import Sandwich, Source, StructuralType
from datetime import datetime, timedelta
import uuid

# Connect to database
repo = Repository("postgresql://sandwich:sandwich@localhost:5432/sandwich")

# Create test source
source = Source(
    url="https://example.com/test",
    domain="example.com",
    content="Test content",
    content_hash="abc123",
    content_type="article"
)
source_id = repo.insert_source(source)

# Create test sandwiches
for i in range(20):
    sandwich = Sandwich(
        name=f"Test Sandwich {i}",
        description=f"A test sandwich for development purposes",
        validity_score=0.5 + (i * 0.025),  # Range 0.5-1.0
        bread_compat_score=0.5 + (i * 0.02),
        containment_score=0.6 + (i * 0.02),
        nontrivial_score=0.55 + (i * 0.02),
        novelty_score=0.65 + (i * 0.015),
        bread_top=f"Top Bread {i}",
        filling=f"Filling {i}",
        bread_bottom=f"Bottom Bread {i}",
        structural_type_id=((i % 10) + 1),  # Rotate through types 1-10
        source_id=source_id,
        assembly_rationale="Test rationale",
        validation_rationale="Test validation",
        sandy_commentary=f"Test commentary for sandwich {i}",
        created_at=datetime.now() - timedelta(days=i)
    )
    repo.insert_sandwich(sandwich)

print("Created 20 test sandwiches")
```

## Development

### Project Structure

```
dashboard/
├── app.py                    # Main landing page
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
├── components/
│   ├── colors.py            # Color palette
│   └── sandwich_card.py     # Reusable card component
├── pages/
│   ├── 1_📊_Live_Feed.py
│   ├── 2_🔍_Browser.py
│   ├── 3_📈_Analytics.py
│   ├── 4_🗺️_Exploration.py
│   ├── 5_✨_Interactive.py
│   └── 6_⚙️_Settings.py
├── utils/
│   ├── db.py               # Database connection
│   └── queries.py          # Cached query functions
└── static/
    └── styles.css          # Custom CSS
```

### Running Tests

```bash
# Run dashboard tests
pytest tests/dashboard/ -v

# Run with coverage
pytest tests/dashboard/ --cov=dashboard --cov-report=html
```

### Adding New Pages

Streamlit automatically detects pages in the `pages/` directory. To add a new page:

1. Create file: `pages/N_🎯_Name.py`
2. Set page config: `st.set_page_config(title="Name", icon="🎯")`
3. Add imports for dashboard utilities
4. Implement page content

### Customizing Styling

Edit `static/styles.css` to customize colors, fonts, and layout.

Colors are defined in `components/colors.py` following SPEC.md Section 14.5.

## Performance

### Caching Strategy

- **Database connection**: Cached via `@st.cache_resource` (persistent)
- **Recent sandwiches**: 5-second TTL (live data)
- **Search results**: 60-second TTL
- **Analytics**: 5-minute TTL (expensive aggregations)

### Query Optimization

- Materialized view (`daily_stats`) for historical analytics
- Indexes on frequently queried columns
- Parameterized queries prevent SQL injection
- RealDictCursor for efficient row conversion

### Troubleshooting

**Dashboard won't load:**
- Check DATABASE_URL is set correctly
- Verify PostgreSQL is running: `docker-compose ps`
- Check logs: `docker-compose logs dashboard`

**No sandwiches appearing:**
- Verify database is initialized: `python scripts/init_db.py`
- Check sandwiches exist: `psql -c "SELECT COUNT(*) FROM sandwiches;"`
- Try creating test data (see above)

**Slow performance:**
- Reduce date range filters
- Lower display limits
- Clear cache: Settings → Clear Dashboard Cache
- Refresh materialized views (coming soon)

**Stale data:**
- Clear Streamlit cache: Settings → Clear Dashboard Cache
- Force page refresh: Press 'R' in browser
- Check TTL values in `utils/queries.py`

## Architecture

### Data Flow

```
User → Streamlit Pages → Query Functions (cached) → Database
                                                   ↓
Agent → Event Bus → Dashboard Updates (live feed)
```

### Real-Time Updates

The Live Feed page uses `@st.fragment(run_every="2s")` to poll the database for new sandwiches without blocking the UI.

When the full agent is implemented, the Event Bus will provide push-based updates for even faster responsiveness.

## Contributing

See SPEC.md Section 14 for full dashboard specification.

## License

Part of the SANDWICH project. See main README.md for license information.

## Credits

Built with:
- [Streamlit](https://streamlit.io/) - Dashboard framework
- [Plotly](https://plotly.com/python/) - Interactive visualizations
- [NetworkX](https://networkx.org/) - Graph analysis
- [PostgreSQL](https://www.postgresql.org/) + [pgvector](https://github.com/pgvector/pgvector) - Database

*"The internet is vast. Somewhere in it: bread."* — Sandy
