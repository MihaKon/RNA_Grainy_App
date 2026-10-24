# Deployment with a self-hosted runner

The production server is behind the university VPN, so GitHub-hosted runners cannot
reach it over SSH. Instead, a GitHub Actions runner runs on the server itself. It opens
an outgoing HTTPS connection to GitHub, waits for jobs, and runs `deploy.sh` locally.

```text
push to main → Build and Test passes → Deploy job → runner on the server → deploy.sh
```

The repository is public, so the runner is set up so that only code merged into `main`
can reach it, and so that a job on it can do nothing except run `deploy.sh`.

## 1. Users on the server

Two users, each with one job:

| User        | Purpose                                                     | Groups   |
| ----------- | ----------------------------------------------------------- | -------- |
| `rnagrainy` | owns `/srv/RNA_Grainy_App`, runs `git` and `docker compose` | `docker` |
| `gh-runner` | runs the GitHub Actions runner; may only start `deploy.sh`  | none     |

`gh-runner` must not be in the `docker` group (that is equivalent to root) and must
not have general `sudo` rights.

If the application already belongs to another user, use that user instead of
`rnagrainy` here, in the sudoers rule below, and in `.github/workflows/deploy.yaml`.

```bash
sudo useradd --create-home --shell /usr/sbin/nologin gh-runner
```

Make sure `gh-runner` cannot change the deployment script or the checkout:

```bash
sudo chown -R rnagrainy: /srv/RNA_Grainy_App
sudo chmod -R o-w /srv/RNA_Grainy_App
```

## 2. Allow the runner to start `deploy.sh`, and nothing else

```bash
sudo visudo -f /etc/sudoers.d/gh-runner-deploy
```

```text
gh-runner ALL=(rnagrainy) NOPASSWD: /usr/bin/bash /srv/RNA_Grainy_App/deploy.sh
```

Check the path with `command -v bash`. The rule allows exactly this command, with
these arguments, as `rnagrainy`. Test it:

```bash
sudo -u gh-runner sudo --non-interactive --set-home -u rnagrainy /usr/bin/bash /srv/RNA_Grainy_App/deploy.sh
sudo -u gh-runner sudo --non-interactive -u rnagrainy id   # must be refused
```

## 3. Install the runner

In the repository: **Settings → Actions → Runners → New self-hosted runner → Linux
x64**. The page shows the current version, the checksum and a registration token that
is valid for one hour.

```bash
sudo mkdir -p /opt/actions-runner
sudo chown gh-runner: /opt/actions-runner
cd /opt/actions-runner

# Download and verify the archive with the commands shown on the GitHub page, as gh-runner:
sudo -u gh-runner curl -o actions-runner.tar.gz -L <URL from the page>
echo "<SHA-256 from the page>  actions-runner.tar.gz" | sha256sum -c
sudo -u gh-runner tar xzf actions-runner.tar.gz

sudo -u gh-runner ./config.sh \
  --url https://github.com/MihaKon/RNA_Grainy_App \
  --token <TOKEN from the page> \
  --name rnagrainy-prod \
  --labels rnagrainy-prod \
  --unattended
```

Run it as a system service, so it starts after a reboot:

```bash
sudo ./svc.sh install gh-runner
sudo ./svc.sh start
sudo ./svc.sh status
```

The runner should now show as **Idle** under Settings → Actions → Runners.

If the server reaches the internet only through a proxy, add it to
`/opt/actions-runner/.env` and restart the service:

```text
https_proxy=http://proxy.example:3128
no_proxy=localhost,127.0.0.1
```

The runner needs outgoing HTTPS (port 443) to `github.com`, `api.github.com` and
`*.actions.githubusercontent.com`. Nothing has to accept incoming connections.

## 4. Repository settings

**Settings → Actions → General**

- _Fork pull request workflows from outside collaborators_: **Require approval for all
  external contributors**.
- _Workflow permissions_: **Read repository contents and packages permissions**.
- Leave _Allow GitHub Actions to create and approve pull requests_ off.

**Settings → Environments → New environment `production`**

- _Deployment branches and tags_: **Selected branches and tags**, add `main`.
- Optional: _Required reviewers_, if every deployment should wait for a click.

**Settings → Rules → Rulesets (or Branches) for `main`**

- Require a pull request before merging, with at least one approval.
- Require the _Build and Test_ status checks to pass.
- Block force pushes and deletions.

**Clean up the SSH deployment**

- Delete the `SSH_KEY`, `SSH_KNOWN_HOSTS`, `SSH_USER` and `SSH_HOST` secrets.
- Remove the matching public key from `~/.ssh/authorized_keys` on the server.

## 5. Deploy

- Automatically: every push to `main` whose _Build and Test_ run succeeds.
- By hand: **Actions → Deploy → Run workflow**, with `main` selected.

## How this keeps the public repository safe

A self-hosted runner runs whatever job is sent to it. In a public repository, the main
risk is a pull request from a fork that edits a workflow to use this runner. These
layers keep that from happening, or limit the damage if it does:

1. **Fork pull requests need approval.** Workflows from outside contributors do not
   start until a maintainer approves them. Before approving, check whether the pull
   request changes anything under `.github/`. Never approve one that adds
   `self-hosted` or `rnagrainy-prod` to a workflow.
2. **The deploy job only runs for `main`.** It runs after a successful _Build and Test_
   run triggered by a push to `main` in this repository, or by hand on `main`. The
   condition checks the event and the repository, because the `branches` filter of
   `workflow_run` alone would also match a fork's branch called `main`.
3. **Only reviewed code reaches `main`.** Branch protection requires a reviewed pull
   request and passing checks.
4. **The job checks out no code.** It runs the `deploy.sh` that is already on the
   server, which deploys `origin/main`.
5. **The runner user has almost no rights.** `gh-runner` can start `deploy.sh` and
   nothing else. It cannot use Docker, `sudo`, or change the application files.
6. **No secrets in GitHub.** No SSH key or password is stored in the repository.

The server is inside the university network, so treat the runner as part of it. Keep
the runner updated (it updates itself by default) and keep the other workflows on
GitHub-hosted runners (`ubuntu-latest`).
