Redpanda manifest (disabled)
--------------------------------

The original `redpanda-deployment.yaml` was removed because it referenced a container image
(`vectorized/redpanda:latest`) that may not be pullable in all environments and caused
`ImagePullBackOff` noise in Minikube demos.

If you need to run a local single-node Redpanda for the PoC, add a supported image tag or
use the official Redpanda Helm chart. Example (manual):

1. Download or change the image to a public tag that your environment can pull.
2. Recreate `redpanda-deployment.yaml` with that image and apply it to the `kafka` namespace.

For now, the bootstrap script prefers an existing Strimzi bootstrap service (`my-cluster-kafka-bootstrap`).
