## Disabled heavy ML trainer Dockerfile
## This file was intentionally disabled for the local PoC because building
## PyTorch + geometric extensions requires a capable build host and many
## minutes of build time. If you want to build the full trainer image,
## restore the original Dockerfile from ml/Dockerfile.disabled and build on
## a machine that has the required toolchain (or in CI).

FROM scratch
LABEL purpose="disabled"
CMD ["/bin/true"]
