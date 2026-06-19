# 🔐 HashiCorp Vault Agent Injector Demo (Python)

This project demonstrates how to inject a secret from HashiCorp Vault into a Kubernetes Pod using the Vault Agent Injector.

The application is a simple Python HTTP server that verifies the injected secret is available.

---

<p align="center">
  <img src="img/schema.png" width="900">
</p>

---

## ✅ Prerequisites

- Kubernetes cluster
- kubectl
- Helm
- Docker
- Vault CLI (optional)

---

## 🚀 1. Install Vault

Add the HashiCorp Helm repository:

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
```

Install Vault in development mode with the injector enabled:

```bash
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
```

Wait until Vault is ready:

```bash
kubectl get pods
```

Expected:

```
vault-0
vault-agent-injector-xxxxx
```

---

## 🔎 2. Access Vault

Open a shell inside the Vault pod:

```bash
kubectl exec -it vault-0 -- sh
```

Verify Vault is running:

```bash
vault status
```

---

## 🗄️ 3. Enable the KV Secrets Engine

```bash
vault secrets enable -path=secret kv-v2
```

---

## 📝 4. Create the Secret

```bash
vault kv put secret/python-vault/realm \
  realm_xml='<realm><users><user><name>john</name></user></users></realm>'
```

Verify:

```bash
vault kv get secret/python-vault/realm
```

---

## 🛡️ 5. Create the Vault Policy

```bash
vault policy write python-vault-read-policy - <<EOF
path "secret/data/python-vault/*" {
  capabilities = ["read"]
}
EOF
```

Verify:

```bash
vault policy read python-vault-read-policy
```

---

## 🔑 6. Enable Kubernetes Authentication

```bash
vault auth enable kubernetes
```

Configure the Kubernetes authentication backend:

```bash
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

---

## 👤 7. Create the Kubernetes Role

```bash
vault write auth/kubernetes/role/python-vault-policy-role \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=python-vault-read-policy \
  ttl=1h
```

Exit the Vault pod:

```bash
exit
```

---

## 🐳 8. Build the Docker Image

```bash
docker build -t python-vault-validation:1.0.0 .
```

If using Kind:

```bash
kind load docker-image python-vault-validation:1.0.0
```

---

## ☸️ 9. Deploy the Application

```bash
kubectl apply -f python-app-deployment.yaml
```

Wait until the pod is ready:

```bash
kubectl get pods
```

Expected:

```
python-vault-app-deployment-xxxxx   2/2   Running
```

---

## 📦 10. Verify the Secret Injection

List injected files:

```bash
kubectl exec deploy/python-vault-app-deployment \
  -c python-vault-container \
  -- ls -la /vault/secrets
```

Expected:

```
realm.xml
```

Display the injected secret:

```bash
kubectl exec deploy/python-vault-app-deployment \
  -c python-vault-container \
  -- cat /vault/secrets/realm.xml
```

---

## 🌐 11. Test the Application

Forward the service:

```bash
kubectl port-forward svc/python-vault-app-service 8080:8080
```

Health endpoint:

```bash
curl http://localhost:8080/_ping
```

Expected:

```json
{
  "status": "ok",
  "app": "python-vault-validation"
}
```

Secret endpoint:

```bash
curl http://localhost:8080/secret-required
```

Expected:

```json
{
  "path": "/vault/secrets/realm.xml",
  "exists": true,
  "size_bytes": 60,
  "first_80_chars": "<realm><users><user><name>john</name></user></users></realm>"
}
```

---

## 🛠️ Troubleshooting

### ❌ Authentication backend not enabled

Error:

```text
no handler for route auth/kubernetes/role/...
```

Solution:

```bash
vault auth enable kubernetes
```

---

### ❌ Backend configuration missing

Error:

```text
could not load backend configuration
```

Solution:

```bash
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
```

---

### ⏳ Pod stuck in Init:0/1

Check the init container:

```bash
kubectl logs deploy/python-vault-app-deployment -c vault-agent-init
```

---

### 🔍 Verify the Secret

Verify the secret exists in Vault:

```bash
vault kv get secret/python-vault/realm
```

Verify the injected file:

```bash
kubectl exec deploy/python-vault-app-deployment \
  -c python-vault-container \
  -- ls -la /vault/secrets
```

---

## 🧹 Cleanup

Delete the application:

```bash
kubectl delete -f python-app-deployment.yaml
```

Uninstall Vault:

```bash
helm uninstall vault
```
