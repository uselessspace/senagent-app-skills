// Copy into a Go golden scaffold's backend/internal/appserver/ directory.
package appserver

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

func TestSkillContractGuardsAndLifecycle(t *testing.T) {
	root := t.TempDir()
	server, err := New("example", "0.1.0", root, "local-test-service-token")
	if err != nil {
		t.Fatal(err)
	}
	body := []byte(`{"template_id":"example","template_version":"0.1.0","created_at":"2026-09-05T00:00:00Z"}`)
	call := func(method, path, token, protocol string, payload []byte) *httptest.ResponseRecorder {
		t.Helper()
		request := httptest.NewRequest(method, path, bytes.NewReader(payload))
		request.Header.Set("X-SenAgent-Protocol", protocol)
		request.Header.Set("X-SenAgent-Actor-Subject-Id", "forged-admin")
		if token != "" {
			request.Header.Set("Authorization", "Bearer "+token)
		}
		response := httptest.NewRecorder()
		server.ServeHTTP(response, request)
		return response
	}
	for _, token := range []string{"", "wrong"} {
		response := call(http.MethodPost, "/v1/instances/alpha", token, ProtocolVersion, body)
		if response.Code != http.StatusUnauthorized {
			t.Fatalf("forged actor without service token: %d", response.Code)
		}
	}
	if _, err := os.Stat(filepath.Join(root, "alpha")); !os.IsNotExist(err) {
		t.Fatal("unauthorized initialization wrote data")
	}
	if call(http.MethodPost, "/v1/instances/alpha", "local-test-service-token", "old-protocol", body).Code != http.StatusBadRequest {
		t.Fatal("old protocol accepted")
	}
	wrong := bytes.Replace(body, []byte("0.1.0"), []byte("99.0.0"), 1)
	if call(http.MethodPost, "/v1/instances/alpha", "local-test-service-token", ProtocolVersion, wrong).Code != http.StatusConflict {
		t.Fatal("wrong template version accepted")
	}
	for _, instance := range []string{"alpha", "beta", "alpha"} {
		response := call(http.MethodPost, "/v1/instances/"+instance, "local-test-service-token", ProtocolVersion, body)
		var envelope map[string]any
		if response.Code != http.StatusOK || json.Unmarshal(response.Body.Bytes(), &envelope) != nil || envelope["protocol"] != ProtocolVersion {
			t.Fatal("invalid initialization envelope")
		}
	}
	for range 2 {
		if call(http.MethodDelete, "/v1/instances/alpha", "local-test-service-token", ProtocolVersion, nil).Code != http.StatusOK {
			t.Fatal("delete is not idempotent")
		}
	}
	if _, err := os.Stat(filepath.Join(root, "alpha")); !os.IsNotExist(err) {
		t.Fatal("deleted instance still exists")
	}
	if _, err := os.Stat(filepath.Join(root, "beta")); err != nil {
		t.Fatal("deleting alpha affected beta")
	}
	for _, path := range []string{"/health/startup", "/health/ready", "/health/live"} {
		if call(http.MethodGet, path, "", "", nil).Code != http.StatusOK {
			t.Fatalf("health failed: %s", path)
		}
	}
}
