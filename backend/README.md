# TOEIC Writing Platform Backend
This is the backend of TOEIC Writing Platform

## I. Components
|Components     |Library / Provider         |Note|
|---------------|---------------------------|----|
|Main App       |FastAPI                    |    |
|DB             |SQLModel (SQLAlchemy)      |    |
|AI             |OpenRouter (with `aiohttp`)|    |
|Package Manager|uv                         |    |

## II. Enviroment Variables

|Name                 |Default                           |Data type           |Note     |
|---------------------|----------------------------------|--------------------|---------|
|DB_URL               |sqlite+aiosqlite:///data/db.sqlite|string              |The string has to be accepted by SQLAlchemy<br>The protocol (the string before `://`) has to include the async dialect (driver) of the DB (for example: `aiosqlite` like `sqlite+aiosqlite://<db_url>`, `asyncpg` like `pg+asyncpg://<db_url>`)<br>Also remember to install the driver via `uv add <driver>`|
|OPENROUTER_URL       |https://ai.hackclub.com/proxy/v1/ |string              |Should be a OpenRouter-SDK-compatible service<br>The URL has to be compatible with `base_url` parameter of AIOHTTP ClientSession (see https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.ClientSession)|
|OPENROUTER_API_KEY * |                                  |string              |         |
|DEFAULT_MODEL        |google/gemini-3-flash-preview     |string              |         |
|QUESTION_MODEL       |DEFAULT_MODEL                     |string              |         |
|REVIEW_MODEL         |DEFAULT_MODEL                     |string              |The model has to be able to see images (the input modilities including `images`)|
|ARTIST_MODEL         |DEFAULT_MODEL                     |string              |The model has to be able to generate images (the output modilities including `images`)|
|LOGGING_LEVEL        |INFO                              |Python logging lever|Not case-sensitive|
|ENV                  |DEV                               |DEV/PROD            |         |

<p>* <span style="color: red">Required</span></p>

## III. Model Usage
### 1. For topic generation:
* Part 1: 10 calls
    * 5 calls for base prompt for image generation and keywords
    * 5 calls for 5 images
* Part 2 & 3: 1 call

### 2. For submission:
* Part 1: 6 calls
    * 5 calls for each image
    * 1 calls for summary 5 responses above
* Part 2 & 3: 1 call

## IV. Endpoints

Please pull this repo, run the backend and visit http://localhost:8000/docs to see the full endpoints docs.

Note that there is a `/file/{file_name}` endpoints that return the content of the file `{file_name}` in `/data/image` directory.

## V. Assets
**Note:** Most of assets is AI-generated

### 1. System prompt
* [Part 1 question generation](./assets/topic/p1/system.txt)
* [Part 1 image generation](./assets/topic/p1/image.txt)
* [Part 2 question generation](./assets/topic/p2/system.txt)
* [Part 3 question generation](./assets/topic/p3/system.txt)

### 2. User submission prompt
* [Part 1](./assets/submit/p1/user.txt)
* [Part 2 & 3](./assets/submit/p2_3/user.txt)

### 3. Themes
* [Part 1](./assets/topic/p1/theme.json)
* [Part 2](./assets/topic/p2/theme.json)
* [Part 3](./assets/topic/p3/theme.json)

### 4. Others
* [P1 Review summary](./assets/submit/p1/summary.txt)
* [JSON Re-request](./assets/error.txt)
* [TailwindCSS Colors](./assets/colors.txt)
