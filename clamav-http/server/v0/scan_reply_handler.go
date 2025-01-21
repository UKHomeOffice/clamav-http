package v0

import (
	"net/http"

	"github.com/dutchcoders/go-clamd"
	"github.com/sirupsen/logrus"
)

type ScanReplyHandler struct {
	Address      string
	Max_file_mem int64
	Logger       *logrus.Logger
}

func (srh *ScanReplyHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	err := r.ParseMultipartForm(srh.Max_file_mem * 1024 * 1024)

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("not okay"))
		return
	}

	files := r.MultipartForm.File["file"]

	if len(files) == 0 {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("empty file\n"))
		return
	}

	f, err := files[0].Open()
	defer f.Close()

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("not okay"))
		return
	}

	c := clamd.NewClamd(srh.Address)
	abort := make(chan bool)
	defer close(abort)

	response, err := c.ScanStream(f, abort)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("not okay"))
		return
	}
	defer r.MultipartForm.RemoveAll()

	result := <-response
	w.WriteHeader(http.StatusOK)
	srh.Logger.Infof("Scanning %v and returning reply", files[0].Filename)
	w.Write([]byte(result.Raw))
	return
}
