package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	corev1 "k8s.io/api/core/v1"
	networkingv1 "k8s.io/api/networking/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
)

// Containment CRD types
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
	ApprovalToken   string  `json:"approvalToken,omitempty"`
}

type ContainmentStatus struct {
	State         string `json:"state,omitempty"` // pending, approved, applied, failed
	AppliedAction string `json:"appliedAction,omitempty"`
	Result        string `json:"result,omitempty"`
	LastUpdate    string `json:"lastUpdate,omitempty"`
}

// ContainmentReconciler handles Containment CRD events
type ContainmentReconciler struct {
	client.Client
	Clientset *kubernetes.Clientset
	Log       log.Logger
}

// Reconcile processes a Containment CR
func (r *ContainmentReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	log := r.Log.WithValues("containment", req.NamespacedName)

	var containment Containment
	if err := r.Get(ctx, req.NamespacedName, &containment); err != nil {
		log.Error(err, "failed to get Containment")
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	// Skip if already applied
	if containment.Status.State == "applied" || containment.Status.State == "failed" {
		return ctrl.Result{}, nil
	}

	log.Info("Processing Containment", "alertID", containment.Spec.AlertID, "confidence", containment.Spec.Confidence)

	// Check confidence threshold
	if containment.Spec.Confidence < 0.7 {
		log.Info("Confidence too low, skipping", "confidence", containment.Spec.Confidence)
		return ctrl.Result{}, r.updateStatus(ctx, &containment, "pending", "confidence_too_low")
	}

	// Require approval for non-dry-run
	if !containment.Spec.DryRun && containment.Spec.ApprovalToken == "" {
		log.Info("Awaiting approval", "alertID", containment.Spec.AlertID)
		return ctrl.Result{RequeueAfter: 30 * time.Second}, r.updateStatus(ctx, &containment, "pending", "awaiting_approval")
	}

	// Execute containment action
	var action string
	var err error
	pod, ns := extractPodNamespace(containment.Spec.AlertID)

	switch containment.Spec.SuggestedAction {
	case "isolate_pod":
		if containment.Spec.DryRun {
			log.Info("DRY RUN: Would isolate pod", "pod", pod, "namespace", ns)
			action = "isolate_pod_dryrun"
		} else {
			err = r.IsolateWithNetworkPolicy(ctx, pod, ns)
			action = "isolate_pod"
		}
	case "evict_pod":
		if containment.Spec.DryRun {
			log.Info("DRY RUN: Would evict pod", "pod", pod, "namespace", ns)
			action = "evict_pod_dryrun"
		} else {
			err = r.EvictPod(ctx, pod, ns)
			action = "evict_pod"
		}
	case "blackhole_traffic":
		if containment.Spec.DryRun {
			log.Info("DRY RUN: Would blackhole traffic", "pod", pod, "namespace", ns)
			action = "blackhole_traffic_dryrun"
		} else {
			err = r.BlackholeViaIstio(ctx, pod, ns)
			action = "blackhole_traffic"
		}
	default:
		log.Info("Unknown action", "action", containment.Spec.SuggestedAction)
		return ctrl.Result{}, r.updateStatus(ctx, &containment, "failed", "unknown_action")
	}

	if err != nil {
		log.Error(err, "failed to apply containment action", "action", action)
		return ctrl.Result{}, r.updateStatus(ctx, &containment, "failed", fmt.Sprintf("error: %v", err))
	}

	log.Info("Containment action applied", "action", action)
	return ctrl.Result{}, r.updateStatus(ctx, &containment, "applied", action)
}

// IsolateWithNetworkPolicy creates a deny-all NetworkPolicy
func (r *ContainmentReconciler) IsolateWithNetworkPolicy(ctx context.Context, pod string, ns string) error {
	policy := &networkingv1.NetworkPolicy{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("isolate-%s", pod),
			Namespace: ns,
		},
		Spec: networkingv1.NetworkPolicySpec{
			PodSelector: metav1.LabelSelector{
				MatchLabels: map[string]string{
					"run": pod, // Adjust label selector as needed
				},
			},
			Ingress:     []networkingv1.NetworkPolicyIngressRule{},
			Egress:      []networkingv1.NetworkPolicyEgressRule{},
			PolicyTypes: []networkingv1.PolicyType{networkingv1.PolicyTypeIngress, networkingv1.PolicyTypeEgress},
		},
	}

	_, err := r.Clientset.NetworkingV1().NetworkPolicies(ns).Create(ctx, policy, metav1.CreateOptions{})
	return err
}

// EvictPod gracefully terminates a pod
func (r *ContainmentReconciler) EvictPod(ctx context.Context, pod string, ns string) error {
	gracePeriod := int64(30)
	return r.Clientset.CoreV1().Pods(ns).Delete(ctx, pod, metav1.DeleteOptions{
		GracePeriodSeconds: &gracePeriod,
	})
}

// BlackholeViaIstio (placeholder) would create an Istio VirtualService to blackhole traffic
func (r *ContainmentReconciler) BlackholeViaIstio(ctx context.Context, pod string, ns string) error {
	// Placeholder: in production, create an Istio VirtualService that routes traffic from pod to a blackhole destination
	// Example: route all outbound traffic to a dummy service that drops packets
	r.Log.Info("Blackhole via Istio: would create VirtualService", "pod", pod, "namespace", ns)
	return nil
}

// updateStatus updates the Containment CR status
func (r *ContainmentReconciler) updateStatus(ctx context.Context, containment *Containment, state string, result string) error {
	containment.Status.State = state
	containment.Status.Result = result
	containment.Status.LastUpdate = time.Now().UTC().Format(time.RFC3339)
	return r.Status().Update(ctx, containment)
}

// extractPodNamespace parses alertID to extract pod and namespace
func extractPodNamespace(alertID string) (string, string) {
	// Simple format: "alert-pod_namespace"
	// In production, use proper parsing
	return "unknown", "default"
}

func main() {
	ctrl.SetLogger(zap.New())
	log := ctrl.Log.WithName("containment-operator")

	config, err := rest.InClusterConfig()
	if err != nil {
		log.Error(err, "error loading in-cluster config")
		os.Exit(1)
	}

	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		log.Error(err, "error creating clientset")
		os.Exit(1)
	}

	mgr, err := ctrl.NewManager(config, ctrl.Options{})
	if err != nil {
		log.Error(err, "error creating manager")
		os.Exit(1)
	}

	if err = (&ContainmentReconciler{
		Client:    mgr.GetClient(),
		Clientset: clientset,
		Log:       log,
	}).SetupWithManager(mgr); err != nil {
		log.Error(err, "error setting up controller")
		os.Exit(1)
	}

	log.Info("Starting containment operator")
	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		log.Error(err, "error running manager")
		os.Exit(1)
	}
}

// SetupWithManager registers the controller
func (r *ContainmentReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&Containment{}).
		Complete(r)
}
