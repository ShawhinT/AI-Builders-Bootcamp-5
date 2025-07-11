## Development Workflow for Architecting a FastAPI Application

After you've talked with customers to get an idea of what your most important functionality might look like you want to build an MVP as quickly as possible. How do I turn that into APIs might frontend can call to get the data it needs?

Highly recommend integrating FastAPI into everything you build because it will make your development process much faster and easier.

### Step 1: Start with the User Story

"As a user, I want to search for all videos by a specific YouTube author"

### Step 2: Design the API Endpoint (Route)

Think: "What URL should the user hit? What should they get back?"

```python
# routes/route.py
@router.get("/author/{author_name}")
async def get_videos_by_author(author_name: str):
    # This will call the service layer
    pass
```

### Step 3: Work Backwards - What Service Method Do I Need?

Think: "What business logic is needed?"

```python
# services/video_service.py
async def get_videos_by_author(self, author_name: str):
    # This needs to call the repository
    videos = await self.video_repo.find_by_author(author_name)
    return videos
```

### Step 4: What Repository Method Do I Need?

Think: "What database query do I need?"

```python
# repositories/video_repository.py
async def find_by_author(self, author_name: str):
    # Direct MongoDB query
    return list(self.collection.find({"author": author_name}))
```

### Step 5: Connect Everything

```python
# Back in routes/route.py
@router.get("/author/{author_name}")
async def get_videos_by_author(
    author_name: str,
    video_service: VideoService = Depends(get_video_service)
):
    videos = await video_service.get_videos_by_author(author_name)
    return videos_list_serial(videos)  # Use schema to serialize
```

## The Thought Process for New Features

1. **Start with the requirement**: What does the user want to do?
    
2. **Design the API first**: What's the cleanest URL/endpoint?
    
3. **Work backwards through layers**:
    
    - Route: What parameters do I receive?
    - Service: What business logic do I need?
    - Repository: What database operations do I need?
4. **Consider edge cases**:
    
    - What if author doesn't exist?
    - What if there are too many results?
    - Should I paginate?
5. **Think about reusability**:
    
    - Can other features use this repository method?
    - Should I make the service method more generic?

## Why This Architecture?

**Separation of Concerns**: Each layer has ONE job

1. **Models Layer**: Define data structures (Pydantic models)
2. **Repository Layer**: ONLY database operations (CRUD) - no business logic
3. **Service Layer**: Where you implement features by orchestrating repositories and external services
4. **Routes Layer**: Where you define API endpoints that call services
5. **Schema Layer**: Specifically for MongoDB serialization (converting Python objects ↔ MongoDB documents)

**Testability**: You can test each layer independently

- Mock the repository to test services
- Mock the service to test routes

**Flexibility**: Easy to change one layer without affecting others

- Switch from MongoDB to PostgreSQL? Only change repository
- Change business rules? Only change service
- New API version? Only change routes

## Common Mistakes to Avoid

1. **Don't put business logic in routes**
    
    ```python
    # BAD - business logic in route
    @router.get("/videos")
    async def get_videos():
        videos = collection.find()  # Direct DB access!
        for video in videos:
            video['score'] = calculate_score(video)  # Business logic!
        return videos
    ```
    
2. **Don't put database queries in services**
    
    ```python
    # BAD - DB query in service
    async def get_videos(self):
        return self.collection.find({})  # Should use repository!
    ```
    
3. **Don't put API calls in repositories**
    
    ```python
    # BAD - external API in repository
    async def get_video(self):
        youtube_data = requests.get("youtube.com/api")  # Wrong layer!
    ```
