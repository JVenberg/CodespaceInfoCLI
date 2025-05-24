# Codespaces Expiration CLI

A command-line tool to list and monitor GitHub Codespaces expiration dates. Helps you keep track of which codespaces are about to expire so you can take action before losing your work.

## Features

- 📅 **Expiration Tracking**: Sort codespaces by expiration date
- 🎨 **Color-Coded Urgency**: Visual indicators for expiration urgency
- 🔍 **Filtering**: Filter by repository, state, or days until expiration
- 📊 **Rich Table Display**: Beautiful terminal output with Rich
- 🔧 **JSON Output**: Machine-readable output for scripting
- 🔐 **Secure Token Handling**: Support for environment variables and .env files

## Installation

### Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) (for running Python scripts with inline dependencies)

### Quick Install

```bash
# Clone this repository
git clone <repository-url>
cd CodespaceExpiration

# Install the command
make install
```

This will create a symlink to the script in `~/.local/bin/codespaces`.

Make sure `~/.local/bin` is in your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Uninstall

```bash
make uninstall
```

## GitHub Token Setup

The tool requires a GitHub Personal Access Token to access the Codespaces API.

### Token Requirements

1. **Must be a "Personal access token (classic)"** (not fine-grained)
2. **Must have "codespace" permission enabled**
3. **Must be authorized for any organization that owns your codespaces**

### Creating a Token

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a descriptive name (e.g., "Codespaces CLI")
4. Select the **`codespace`** scope
5. If you use organization-owned codespaces, click "Configure SSO" and authorize the token for those organizations
6. Click "Generate token" and copy the token

### Providing the Token

You can provide the token in three ways (in order of precedence):

1. **Command line parameter**:

   ```bash
   codespaces --token ghp_your_token_here
   ```

2. **Environment variable**:

   ```bash
   export GITHUB_TOKEN=ghp_your_token_here
   codespaces
   ```

3. **`.env` file**:

   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env and add your token
   # GITHUB_TOKEN=ghp_your_token_here
   ```

## Usage

### Basic Usage

```bash
# List all codespaces sorted by expiration date
codespaces
```

### Filtering Options

```bash
# Show only codespaces expiring within 7 days
codespaces --days 7

# Filter by repository name (partial match)
codespaces --repo web

# Filter by state
codespaces --state Shutdown

# Combine filters
codespaces --days 14 --repo web --state Available
```

### Output Formats

```bash
# Default: Rich table output
codespaces

# JSON output for scripting
codespaces --json

# JSON with filters
codespaces --days 7 --json | jq '.[] | .display_name'
```

## Command Line Options

| Option    | Short | Description                                           |
| --------- | ----- | ----------------------------------------------------- |
| `--token` | `-t`  | GitHub personal access token (overrides .env)         |
| `--days`  | `-d`  | Show only codespaces expiring within N days           |
| `--repo`  | `-r`  | Filter by repository name (partial match)             |
| `--state` | `-s`  | Filter by codespace state (e.g., Available, Shutdown) |
| `--json`  | `-j`  | Output as JSON instead of table                       |
| `--help`  |       | Show help message                                     |

## Understanding the Output

### Table Columns

- **Display Name**: The friendly name of the codespace
- **Repository**: The repository the codespace is for
- **State**: Current state (Available, Shutdown, etc.)
- **Expires In**: Time until expiration with color coding
- **Last Used**: Date when the codespace was last accessed
- **Machine**: The machine type and specs
- **Git Status**: Shows uncommitted/unpushed changes

### Color Coding

**Expiration Urgency:**

- 🔴 **Red**: Less than 7 days
- 🟡 **Yellow**: 7-14 days
- 🟢 **Green**: More than 14 days
- ⚪ **Gray**: No expiration (active codespaces)

**State Colors:**

- 🟢 **Green**: Available
- 🟡 **Yellow**: Shutdown
- 🔴 **Red**: Other states

## Examples

### Check for urgent expirations

```bash
# Show codespaces expiring in the next 3 days
codespaces --days 3
```

### Monitor specific repository

```bash
# Check all web repository codespaces
codespaces --repo web
```

### Script integration

```bash
# Get count of codespaces expiring soon
expiring_count=$(codespaces --days 7 --json | jq length)
echo "You have $expiring_count codespaces expiring within 7 days"

# List names of expiring codespaces
codespaces --days 7 --json | jq -r '.[] | .display_name'
```

### Cron job example

```bash
# Add to crontab to check daily at 9 AM
0 9 * * * /home/user/.local/bin/codespaces --days 7 > /dev/null || echo "Codespaces expiring soon!"
```

## Troubleshooting

### Token Issues

If you get authentication errors:

1. Verify your token has the `codespace` scope
2. Check if the token is authorized for your organization
3. Ensure the token hasn't expired
4. Try regenerating the token

### PATH Issues

If `codespaces` command is not found:

1. Check if `~/.local/bin` is in your PATH
2. Add to your shell configuration file (`.bashrc`, `.zshrc`, etc.):
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```
3. Reload your shell configuration

### Python/uv Issues

If the script doesn't run:

1. Ensure you have Python 3.9+ installed
2. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. Try running directly: `uv run codespaces.py`

## Development

The script uses inline script dependencies (PEP 723) which are automatically handled by `uv`. Dependencies include:

- `typer[all]` - CLI framework
- `requests` - HTTP client
- `rich` - Terminal formatting
- `python-dotenv` - Environment variable handling

## License

MIT License - See LICENSE file for details
