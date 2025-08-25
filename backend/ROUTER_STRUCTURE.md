# API Router Structure

This document explains the router architecture implemented in the Vesta FastAPI application with versioning and subtags support.

## Router Hierarchy

```
main.py
├── FastAPI app
└── api_router_v1 (from app.api.v1) at prefix="/api/v1"
    ├── auth.router at "/api/v1/auth" (tags: ["authentication"])
    │   ├── POST /api/v1/auth/login (subtags: ["authentication", "login"])
    │   ├── POST /api/v1/auth/logout (subtags: ["authentication", "logout"])
    │   ├── POST /api/v1/auth/register (subtags: ["authentication", "registration"])
    │   └── GET /api/v1/auth/me (subtags: ["authentication", "profile"])
    ├── items.router at "/api/v1/items" (tags: ["items"])
    │   ├── GET /api/v1/items/ (subtags: ["items", "read"])
    │   ├── GET /api/v1/items/{item_id} (subtags: ["items", "read"])
    │   ├── POST /api/v1/items/ (subtags: ["items", "create"])
    │   ├── PUT /api/v1/items/{item_id} (subtags: ["items", "update"])
    │   └── DELETE /api/v1/items/{item_id} (subtags: ["items", "delete"])
    ├── users.router at "/api/v1/users" (tags: ["users"])
    │   ├── GET /api/v1/users/ (subtags: ["users", "management"])
    │   ├── GET /api/v1/users/{user_id} (subtags: ["users", "management"])
    │   ├── POST /api/v1/users/ (subtags: ["users", "administration"])
    │   ├── PUT /api/v1/users/{user_id} (subtags: ["users", "administration"])
    │   └── DELETE /api/v1/users/{user_id} (subtags: ["users", "administration"])
    ├── GET /api/v1/ (API root)
    └── GET /api/v1/status (API status)
```

## File Structure

```
app/
├── __init__.py
└── api/
    └── v1/                 # API Version 1
        ├── __init__.py     # Exports api_router
        ├── routes.py       # Main router that includes all sub-routers
        ├── auth.py         # Authentication endpoints
        ├── items.py        # Items CRUD endpoints
        └── users.py        # Users CRUD endpoints
```

## Subtags Implementation

FastAPI supports hierarchical organization through multiple tags. Each endpoint can have multiple tags for better categorization:

### Main Categories:

- **Authentication**: User authentication and authorization
- **Items**: Item management operations
- **Users**: User management operations

### Operation Types (Subtags):

- **Read**: GET operations for retrieving data
- **Create**: POST operations for creating new resources
- **Update**: PUT/PATCH operations for modifying existing resources
- **Delete**: DELETE operations for removing resources
- **Login**: Login-specific authentication operations
- **Registration**: User registration operations
- **Profile**: User profile management
- **Management**: General read/view operations
- **Administration**: Administrative write operations

## How to Add New Routers

## How to Add New Routers

1. Create a new file in `app/api/v1/` (e.g., `products.py`)
2. Define your router with subtags:

   ```python
   from fastapi import APIRouter

   router = APIRouter()

   @router.get("/", tags=["products", "read"])
   async def get_products():
       return {"products": []}

   @router.post("/", tags=["products", "create"])
   async def create_product(product_data: dict):
       return {"message": "Product created", "data": product_data}
   ```

3. Import and include it in `app/api/v1/routes.py`:

   ```python
   from . import products

   api_router.include_router(
       products.router,
       prefix="/products",
       tags=["products"]
   )
   ```

## Tag Metadata Configuration

You can enhance your API documentation by adding tag metadata in `main.py`:

```python
tags_metadata = [
    {
        "name": "authentication",
        "description": "User authentication and authorization operations",
    },
    {
        "name": "items",
        "description": "Operations with items. CRUD functionality for managing items.",
    },
    {
        "name": "users",
        "description": "User management operations. Admin functionality.",
    },
    {
        "name": "read",
        "description": "Read operations for retrieving data",
    },
    {
        "name": "create",
        "description": "Create operations for new resources",
    },
    {
        "name": "update",
        "description": "Update operations for existing resources",
    },
    {
        "name": "delete",
        "description": "Delete operations for removing resources",
    },
]

app = FastAPI(
    title="Vesta API",
    description="A FastAPI application with nested router structure",
    version="1.0.0",
    openapi_tags=tags_metadata
)
```

## API Versioning

The current structure supports API versioning:

- **v1**: Current API version at `/api/v1/`
- **Future versions**: Can be added as `app/api/v2/`, `app/api/v3/`, etc.
- **Backward compatibility**: Multiple versions can run simultaneously

## Benefits

- **Modular**: Each feature has its own router file
- **Scalable**: Easy to add new routers without modifying existing code
- **Organized**: Clear separation of concerns with versioning
- **Tagged**: Hierarchical API documentation grouping with subtags
- **Prefixed**: Clean URL structure with version control
- **Maintainable**: Version-specific changes don't affect other versions
- **Documentation**: Rich OpenAPI documentation with categorized endpoints
