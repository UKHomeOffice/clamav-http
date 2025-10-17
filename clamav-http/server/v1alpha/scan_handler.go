package v1alpha

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/dutchcoders/go-clamd"
	"github.com/sirupsen/logrus"
)

type ScanResponse struct {
	Status      string `json:"status"`
	Description string `json:"description"`
	Raw         string `json:"raw"`
	Message     string `json:"message"`
}

type ErrorResponse struct {
	Error string `json:"error"`
}

func writeError(w http.ResponseWriter, wantJSON bool, status int, message string) {
	w.WriteHeader(status)
	if wantJSON {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(ErrorResponse{Error: message})
	} else {
		w.Write([]byte(message))
	}
}

type ScanHandler struct {
	Address      string
	Max_file_mem int64
	Logger       *logrus.Logger
}

const (
	scan_error_0 = iota
	scan_error_1 = iota
	scan_error_2 = iota
)

func (sh *ScanHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	wantJSON := strings.Contains(r.Header.Get("Accept"), "application/json")

	err := r.ParseMultipartForm(sh.Max_file_mem * 1024 * 1024)
	if err != nil {
		sh.Logger.Errorf("scan error %d: %s", scan_error_0, err.Error())
		writeError(w, wantJSON, http.StatusBadRequest, "Invalid request: "+err.Error())
		return
	}

	files := r.MultipartForm.File["file"]
	if len(files) == 0 {
		writeError(w, wantJSON, http.StatusNoContent, "empty file")
		return
	}

	f, err := files[0].Open()
	defer f.Close()
	if err != nil {
		sh.Logger.Errorf("scan error %d: %s", scan_error_1, err.Error())
		writeError(w, wantJSON, http.StatusInternalServerError, err.Error())
		return
	}

	c := clamd.NewClamd(sh.Address)
	abort := make(chan bool)
	defer close(abort)

	response, err := c.ScanStream(f, abort)
	if err != nil {
		sh.Logger.Errorf("scan error %d: %s", scan_error_2, err.Error())
		writeError(w, wantJSON, http.StatusInternalServerError, err.Error())
		return
	}
	defer r.MultipartForm.RemoveAll()

	result := <-response

	var status int
	var message string

	switch result.Status {
	case "OK":
		status = http.StatusOK
		message = "OK"
		sh.Logger.Infof("Scanning %v: RES_OK", files[0].Filename)
	case "FOUND":
		status = http.StatusForbidden
		message = "FOUND"
		sh.Logger.Infof("Scanning %v: RES_FOUND", files[0].Filename)
	case "ERROR":
		status = http.StatusBadRequest
		message = "ERROR"
		sh.Logger.Infof("Scanning %v: RES_ERROR", files[0].Filename)
	case "PARSE_ERROR":
		status = http.StatusPreconditionFailed
		message = "PARSE_ERROR"
		sh.Logger.Infof("Scanning %v: RES_PARSE_ERROR", files[0].Filename)
	default:
		status = http.StatusNotImplemented
		message = "NOT_IMPLEMENTED"
	}

	w.WriteHeader(status)

	if wantJSON {
		w.Header().Set("Content-Type", "application/json")
		response := ScanResponse{
			Status:      result.Status,
			Description: result.Description,
			Raw:         result.Raw,
			Message:     message,
		}
		json.NewEncoder(w).Encode(response)
	} else {
		w.Write([]byte("AV Response : " + message + "\n"))
	}
	return
}
