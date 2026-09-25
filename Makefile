# Readable shortcuts for the disposable lab. The ./lab wrapper does the real
# Docker/Podman selection and forwards commands into the pinned image.

.DEFAULT_GOAL := help
.PHONY: help start list state check shell reset reset-all forge forge-status forge-stop verify

ifdef LAB_RUNTIME
RUN = LAB_RUNTIME=$(LAB_RUNTIME) ./lab
else
RUN = ./lab
endif

help: ## Show the common lab commands.
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "%-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

start: ## Build images, start Forgejo, and create the interactive fixture.
	$(RUN) start

list: ## List the available experiments.
	$(RUN) scenario list

state: ## Show the active fixture state.
	$(RUN) state

check: ## Run formatting, linting, tests, scenarios, and doctor checks.
	$(RUN) check

shell: ## Open a shell inside the lab container.
	$(RUN) shell

reset: ## Reset the interactive fixture while retaining evidence.
	$(RUN) reset

reset-all: ## Remove generated scenario fixtures while retaining evidence.
	$(RUN) reset --all

forge: ## Run the hosted Forgejo PR experiment.
	$(RUN) forge run

forge-status: ## Show the latest Forgejo experiment status.
	$(RUN) forge status

forge-stop: ## Stop Forgejo while preserving its named volume.
	$(RUN) forge stop

verify: ## Run every registered core scenario.
	$(RUN) scenario verify
