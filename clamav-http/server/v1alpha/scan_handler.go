package v1alpha

import (
	"net/http"

	"github.com/dutchcoders/go-clamd"
	"github.com/sirupsen/logrus"
)

type ScanHandler struct {
	Address      string
	Max_file_mem int64
	Logger       *logrus.Logger
}

func (sh *ScanHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	err := r.ParseMultipartForm(sh.Max_file_mem * 1024 * 1024)

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(err.Error()))
		return
	}

	files := r.MultipartForm.File["file"]

	if len(files) == 0 {
		w.WriteHeader(http.StatusNoContent)
		w.Write([]byte("empty file\n"))
		return
	}

	f, err := files[0].Open()
	defer f.Close()

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(err.Error()))
		return
	}

	c := clamd.NewClamd(sh.Address)
	response, err := c.ScanStream(f, make(chan bool))

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(err.Error()))
		return
	}

	result := <-response
	if result.Status == "FOUND" {
		w.WriteHeader(http.StatusForbidden)
		sh.Logger.Infof("Scanning %v: found", files[0].Filename)
		w.Write([]byte("Everything ok : false\n"))
	} else {
		w.WriteHeader(http.StatusOK)
		sh.Logger.Infof("Scanning %v: clean", files[0].Filename)
		w.Write([]byte("Everything ok : true\n"))
	}

	return
}
