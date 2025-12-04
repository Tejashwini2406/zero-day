package main

import (
    "context"
    "fmt"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    netv1 "k8s.io/api/networking/v1"
    "sigs.k8s.io/controller-runtime/pkg/client"
)

// handleAlert applies a conservative NetworkPolicy to isolate a target Pod label.
func handleAlert(ctx context.Context, c client.Client, alertName string, ns string, targetApp string) error {
    np := &netv1.NetworkPolicy{
        ObjectMeta: metav1.ObjectMeta{
            Name: fmt.Sprintf("isolate-%s", targetApp),
            Namespace: ns,
        },
        Spec: netv1.NetworkPolicySpec{
            PodSelector: metav1.LabelSelector{MatchLabels: map[string]string{"app": targetApp}},
            PolicyTypes: []netv1.PolicyType{netv1.PolicyTypeIngress, netv1.PolicyTypeEgress},
            Ingress: []netv1.NetworkPolicyIngressRule{},
            Egress: []netv1.NetworkPolicyEgressRule{},
        },
    }
    return c.Create(ctx, np)
}
package main

import (
	"context"
	"fmt"
	"log"

	corev1 "k8s.io/api/core/v1"
	networkingv1 "k8s.io/api/networking/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	ctrl "sigs.k8s.io/controller-runtime"
)

// Containment CRD stub (would be auto-generated from openapi schema in real code)
type Containment struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`
	Spec               ContainmentSpec   `json:"spec,omitempty"`
	Status             ContainmentStatus `json:"status,omitempty"`
}

type ContainmentSpec struct {
	AlertID         string  `json:"alertID,omitempty"`
	Confidence      float64 `json:"confidence,omitempty"`
	SuggestedAction string  `json:"suggestedAction,omitempty"`
	DryRun          bool    `json:"dryRun,omitempty"`
	Explanation     string  `json:"explanation,omitempty"`
}

type ContainmentStatus struct {
	AppliedAction string `json:"appliedAction,omitempty"`
	Result        string `json:"result,omitempty"`
}

func IsolateWithNetworkPolicy(ctx context.Context, clientset kubernetes.Interface, pod *corev1.Pod) error {
	ns := pod.Namespace
	podName := pod.Name

	// Create a deny-all NetworkPolicy for this pod
	policy := &networkingv1.NetworkPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("isolate-%s", podName),
			Namespace: ns,
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: metav1.LabelSelector{
				MatchLabels: map[string]string{
					"pod": podName,
				},
			},
			Ingress: []networkingv1.NetworkPolicyIngressRule{},
			Egress:  []networkingv1.NetworkPolicyEgressRule{},
			PolicyTypes: []networkingv1.PolicyType{
				networkingv1.PolicyTypeIngress,
				networkingv1.PolicyTypeEgress,
			},
		},
	}

	_, err := clientset.NetworkingV1().NetworkPolicies(ns).Create(ctx, policy, metav1.CreateOptions{})
	return err
}

func CordonPod(ctx context.Context, clientset kubernetes.Interface, pod *corev1.Pod) error {
	// Evict pod (safe eviction)
	eviction := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:      pod.Name,
			Namespace: pod.Namespace,
		},
	}
	return clientset.CoreV1().Pods(pod.Namespace).Delete(ctx, eviction.Name, metav1.DeleteOptions{GracePeriodSeconds: &[]int64{30}[0]})
}

func main() {
	config, err := rest.InClusterConfig()
	if err != nil {
		log.Fatalf("Error loading in-cluster config: %v", err)
	}

	clientsetObj, err := kubernetes.NewForConfig(config)
	if err != nil {
		log.Fatalf("Error creating kubernetes clientset: %v", err)
	}

	mgr, err := ctrl.NewManager(config, ctrl.Options{})
	if err != nil {
		log.Fatalf("Unable to start manager: %v", err)
	}

	// Placeholder: in production, register Containment controller here
	_ = clientsetObj // suppress unused warning
	fmt.Println("Containment operator running. Waiting for Containment CRDs...")
	log.Println("Use ctl to apply Containment resources and trigger containment actions")

	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		log.Fatalf("problem running manager: %v", err)
	}
}
