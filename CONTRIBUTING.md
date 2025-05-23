# Contributing to auto-mcs

We appreciate your interest in contributing to auto-mcs! To maintain quality, consistency, and clarity in the development process, please review and adhere to the following guidelines before submitting a pull request.

---

## 🚧 Contribution Guidelines

### 1. Check Existing Issues First  
Before opening a new issue or feature request, please check the [issue tracker](https://github.com/macarooni-man/auto-mcs/issues) to see if one already exists. If you can contribute to solving an existing issue, that’s even better!

### 2. PRs Are Not for Feature Brainstorming  
All pull requests must be based on an existing and discussed issue. If you have an idea for a new feature, open a [feature request issue](https://github.com/macarooni-man/auto-mcs/issues) first. Do not use pull requests as a substitute for conversation.

### 3. Target the Correct Branch  
All pull requests must be made against the `dev` branch.  
Please don't open pull requests against `main`. This can cause merge conflicts and disrupt the release pipeline.

### 4. PRs Must Be Complete and Tested  
Please do not submit partial or experimental features.  
Pull requests must be:
- Fully implemented
- Tested and working across intended environments
- Able to run without breaking existing functionality

Commit locally to the forked branch, and submit the PR when development is complete. Feel free to link questions in your branch to the attached issue, detailed below.

### 5. PRs Must Reference an Issue  
All pull requests must **link to a specific issue** whether that's a bug or a feature request. This helps us keep the project organized and traceable.

### 6. Ask Questions — Don’t Assume! 
The codebase is large and undocumented at this time. If you're unsure how something works:
- Ask questions! We're more than happy to explain how things work
- Don’t try to fix complex systems by guessing as this can cause issues with unrelated functionality due to how interdependent the codebase is.
- The best place to ask questions and get help is our [Discord](https://discord.gg/dShCFbgNYJ).

---

## Cross-Platform Test Methodology

auto-mcs is built to run on Windows, macOS, and Linux. Thorough testing is crucial to maintaining the stability of the software across all platforms.

### Operating System Testing  
Please test your contribution on as many of the following platforms as possible:
- Windows
- macOS (Apple Silicon preferred)
- Linux (Ubuntu/Debian-based preferred)

If you only have access to one platform, **submit your pull request anyway**, and let us know which platform you tested in the PR description. We will help test the changes on the others.

### Telepath Testing
If your contribution affects [Telepath](https://www.auto-mcs.com/guides/telepath), please test both server modes:
- **GUI mode** (standard graphical interface)
- **Headless mode** (e.g. Docker or a binary deployment with `--headless`)

Additionally, please include detailed information of the platforms tested of both the host and client:
- Host: Ubuntu 22.04 Server (headless)
- Client: Windows 10

### amscript Testing
If your contribution affects [amscript](https://www.auto-mcs.com/guides/amscript), please include example scripts in the description of your PR. Preferably a comparison with something that either doesn't work/doesn't exist in the current version, and an example that includes the changes in the PR.


---

## Examples

### ✅ A Good Pull Request:
> **Implements compression for `.amb` files**  
> Tested on Windows and macOS (provide a link to the successful build)  
> References Issue #1234  
> Fully functional for both GUI and headless Telepath instances.

### 🚫 A Bad Pull Request:
> **WIP server optimization changes**  
> (Breaks startup, untested, no linked issue, etc.)

---

Thanks for helping to make auto-mcs better! Feel free to reach out on our [Discord](https://discord.gg/dShCFbgNYJ) with any questions.
