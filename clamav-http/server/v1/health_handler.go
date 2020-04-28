package v1

import (
	"net/http"

	"github.com/sirupsen/logrus"
)

type HealthHandler struct {
	Healthy bool
	Logger  *logrus.Logger
}

func (hh *HealthHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if hh.Healthy {
		hh.Logger.Infof("health check: ok")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Healthy\n"))
		return
	}
	hh.Logger.Infof("health check: not ok")
	w.WriteHeader(http.StatusInternalServerError)
	w.Write([]byte("Unhealthy\n"))
}
