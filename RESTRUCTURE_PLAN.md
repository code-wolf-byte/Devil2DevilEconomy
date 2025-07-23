# 🏗️ Devil2Devil Economy - Codebase Restructure Plan

## 🎯 Goals
- **Separation of Concerns**: Clear boundaries between Discord bot, web app, and shared services
- **Configuration Management**: Centralized, environment-aware configuration
- **Maintainability**: Consistent patterns, easy testing, clear documentation
- **Scalability**: Modular design that can grow with requirements
- **Developer Experience**: Easy setup, clear structure, comprehensive tooling

## 📁 Proposed New Directory Structure

```
devil2devil_economy/
├── README.md
├── CHANGELOG.md
├── pyproject.toml                 # Modern Python packaging
├── requirements-dev.txt           # Development dependencies
├── requirements.txt               # Production dependencies
├── docker-compose.yml
├── docker-compose.dev.yml         # Development overrides
├── Dockerfile
├── .env.example
├── .gitignore
├── .dockerignore
│
├── app/                          # Main application package
│   ├── __init__.py
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   ├── base.py              # Base configuration
│   │   ├── development.py       # Dev-specific settings
│   │   ├── production.py        # Prod-specific settings
│   │   └── testing.py           # Test-specific settings
│   │
│   ├── core/                    # Core business logic
│   │   ├── __init__.py
│   │   ├── database.py          # Database initialization
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── extensions.py        # Flask extensions
│   │   └── permissions.py       # Permission utilities
│   │
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── base.py             # Base model class
│   │   ├── user.py             # User model
│   │   ├── product.py          # Product model
│   │   ├── purchase.py         # Purchase model
│   │   ├── achievement.py      # Achievement models
│   │   └── economy.py          # Economy settings
│   │
│   ├── services/               # Business logic services
│   │   ├── __init__.py
│   │   ├── user_service.py     # User management
│   │   ├── product_service.py  # Product management
│   │   ├── purchase_service.py # Purchase processing
│   │   ├── economy_service.py  # Economy calculations
│   │   ├── file_service.py     # File handling
│   │   └── discord_service.py  # Discord integration
│   │
│   ├── web/                    # Flask web application
│   │   ├── __init__.py
│   │   ├── app.py              # Flask app factory
│   │   ├── auth/               # Authentication blueprint
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── views.py
│   │   ├── main/               # Main routes blueprint
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── views.py
│   │   ├── admin/              # Admin blueprint
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── views.py
│   │   ├── api/                # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   └── routes.py
│   │   └── middleware/         # Custom middleware
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       └── logging.py
│   │
│   ├── discord_bot/            # Discord bot application
│   │   ├── __init__.py
│   │   ├── bot.py              # Bot initialization
│   │   ├── cogs/               # Bot command modules
│   │   │   ├── __init__.py
│   │   │   ├── economy.py
│   │   │   ├── admin.py
│   │   │   └── user.py
│   │   ├── events/             # Event handlers
│   │   │   ├── __init__.py
│   │   │   ├── message.py
│   │   │   ├── reaction.py
│   │   │   └── member.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── embeds.py
│   │       └── helpers.py
│   │
│   ├── shared/                 # Shared utilities
│   │   ├── __init__.py
│   │   ├── constants.py        # Application constants
│   │   ├── decorators.py       # Custom decorators
│   │   ├── utils.py            # Utility functions
│   │   ├── validators.py       # Input validation
│   │   └── formatters.py       # Data formatting
│   │
│   └── tasks/                  # Background tasks
│       ├── __init__.py
│       ├── maintenance.py      # Maintenance tasks
│       ├── backup.py           # Backup operations
│       └── monitoring.py       # Health checks
│
├── migrations/                 # Database migrations
│   ├── README
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── static/                     # Static web assets
│   ├── css/
│   ├── js/
│   ├── images/
│   └── uploads/               # User uploads (volume mounted)
│
├── templates/                 # Jinja2 templates
│   ├── base.html
│   ├── auth/
│   ├── main/
│   └── admin/
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Pytest configuration
│   ├── unit/                 # Unit tests
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   └── test_utils.py
│   ├── integration/          # Integration tests
│   │   ├── test_api.py
│   │   ├── test_discord.py
│   │   └── test_web.py
│   ├── fixtures/             # Test data
│   └── helpers/              # Test utilities
│
├── scripts/                  # Utility scripts
│   ├── setup.py             # Environment setup
│   ├── migrate.py           # Database migration runner
│   ├── backup.py            # Backup management
│   ├── deploy.py            # Deployment automation
│   └── health_check.py      # System health verification
│
├── docs/                    # Documentation
│   ├── README.md
│   ├── api.md
│   ├── deployment.md
│   ├── development.md
│   └── architecture.md
│
├── docker/                  # Docker configuration
│   ├── Dockerfile.web
│   ├── Dockerfile.bot
│   ├── Dockerfile.dev
│   └── docker-entrypoint.sh
│
└── deploy/                  # Deployment configuration
    ├── docker-compose.prod.yml
    ├── nginx.conf
    ├── systemd/
    └── k8s/                # Kubernetes manifests (future)
```

## 🏛️ Architectural Principles

### 1. **Application Factory Pattern**
```python
# app/web/app.py
def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.web.main import bp as main_bp
    from app.web.auth import bp as auth_bp
    from app.web.admin import bp as admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app
```

### 2. **Service Layer Pattern**
```python
# app/services/purchase_service.py
class PurchaseService:
    def __init__(self, db_session, discord_service):
        self.db = db_session
        self.discord = discord_service
    
    def process_purchase(self, user_id: str, product_id: int) -> PurchaseResult:
        # Business logic here
        # Validation, balance checks, product availability
        # Purchase creation, inventory updates
        # Discord notifications, role assignments
        pass
    
    def handle_digital_delivery(self, purchase: Purchase) -> DeliveryResult:
        # Handle different delivery types
        pass
```

### 3. **Configuration Management**
```python
# app/config/base.py
class Config:
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Discord
    DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
    DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID')
    
    # File uploads
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev.db'

class ProductionConfig(Config):
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        # Production-specific setup
        import logging
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            'logs/app.log', maxBytes=10240, backupCount=10
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
```

### 4. **Dependency Injection**
```python
# app/core/dependencies.py
class ServiceContainer:
    def __init__(self, app=None):
        self.app = app
        self._services = {}
    
    def init_app(self, app):
        self.app = app
        app.container = self
    
    def register(self, name: str, factory):
        self._services[name] = factory
    
    def get(self, name: str):
        if name not in self._services:
            raise ValueError(f"Service {name} not registered")
        return self._services[name]()

# Usage in routes
def purchase_product(product_id):
    purchase_service = current_app.container.get('purchase_service')
    result = purchase_service.process_purchase(current_user.id, product_id)
```

## 🔄 Migration Strategy

### Phase 1: Foundation (Week 1-2)
1. **Setup new structure**
   ```bash
   mkdir -p app/{config,core,models,services,web,discord_bot,shared,tasks}
   # Create __init__.py files
   ```

2. **Configuration refactor**
   - Move from `shared.py` to proper config classes
   - Environment-specific configurations
   - Validation of required environment variables

3. **Database models separation**
   - Extract models from `shared.py`
   - Create proper model relationships
   - Add model validation methods

### Phase 2: Service Layer (Week 3-4)
1. **Create service classes**
   - User management service
   - Product/Purchase services
   - Discord integration service
   - File handling service

2. **Refactor web routes**
   - Move business logic to services
   - Implement dependency injection
   - Add proper error handling

### Phase 3: Discord Bot Restructure (Week 5-6)
1. **Separate bot from web app**
   - Independent bot initialization
   - Event-driven architecture
   - Shared service layer

2. **Cog reorganization**
   - Separate admin, user, and economy cogs
   - Event handlers in separate modules
   - Utility functions organization

### Phase 4: Testing & Deployment (Week 7-8)
1. **Comprehensive test suite**
   - Unit tests for services
   - Integration tests for APIs
   - Discord bot testing framework

2. **Deployment automation**
   - Docker multi-stage builds
   - Health check endpoints
   - Monitoring and logging

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/unit/test_purchase_service.py
def test_purchase_insufficient_balance():
    user = User(balance=10)
    product = Product(price=20)
    
    service = PurchaseService(db.session, mock_discord)
    result = service.process_purchase(user.id, product.id)
    
    assert not result.success
    assert result.error == "Insufficient balance"
```

### Integration Tests
```python
# tests/integration/test_purchase_flow.py
def test_complete_purchase_flow(client, auth_user):
    # Test full purchase workflow
    response = client.post('/purchase/1', 
                          headers=auth_headers(auth_user))
    
    assert response.status_code == 200
    # Verify database changes
    # Verify Discord notifications
```

## 🚀 Deployment Improvements

### Multi-stage Docker Build
```dockerfile
# docker/Dockerfile.web
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.web.app:create_app()"]
```

### Health Check Endpoints
```python
# app/web/api/health.py
@bp.route('/health')
def health_check():
    checks = {
        'database': check_database_connection(),
        'discord': check_discord_connection(),
        'filesystem': check_file_permissions(),
    }
    
    status = 200 if all(checks.values()) else 503
    return jsonify(checks), status
```

## 📊 Benefits of New Structure

### ✅ **Immediate Benefits**
- Clear separation of concerns
- Easier testing and debugging
- Consistent code patterns
- Better error handling
- Proper configuration management

### ✅ **Long-term Benefits**
- Scalable architecture
- Easy feature additions
- Team collaboration friendly
- Documentation-driven development
- Monitoring and observability

### ✅ **Developer Experience**
- Fast local setup
- Clear development guidelines
- Automated testing
- Easy deployment process
- Comprehensive documentation

## 🎯 Implementation Checklist

### Preparation
- [ ] Create new repository branch
- [ ] Set up new directory structure
- [ ] Create configuration system
- [ ] Set up testing framework

### Migration Tasks
- [ ] Extract models from `shared.py`
- [ ] Create service layer
- [ ] Refactor web routes
- [ ] Restructure Discord bot
- [ ] Update deployment scripts
- [ ] Migrate tests
- [ ] Update documentation

### Validation
- [ ] All tests pass
- [ ] Performance benchmarks meet requirements
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Team training completed

This restructured approach transforms your codebase from a monolithic structure into a maintainable, scalable application following modern Python best practices. The clear separation of concerns makes it much easier to maintain, test, and extend. 