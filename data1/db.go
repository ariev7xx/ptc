
package main

import (
	"database/sql"
	"encoding/hex"
	"fmt"
	"log"
	"os"

	bolt "go.etcd.io/bbolt"
	_ "modernc.org/sqlite"
)

func main() {
	source := "psiphon.boltdb"
	output := "psiphon.db"

	_ = os.Remove(output)

	src, err := bolt.Open(source, 0400, &bolt.Options{
		ReadOnly: true,
	})
	if err != nil {
		log.Fatal(err)
	}
	defer src.Close()

	dst, err := sql.Open("sqlite", output)
	if err != nil {
		log.Fatal(err)
	}
	defer dst.Close()

	_, err = dst.Exec(`
	PRAGMA journal_mode=WAL;

	CREATE TABLE buckets (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		parent_id INTEGER,
		name TEXT NOT NULL
	);

	CREATE TABLE records (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		bucket_id INTEGER NOT NULL,
		key_hex TEXT NOT NULL,
		key_text TEXT,
		value_text TEXT,
		value_blob BLOB,
		value_type TEXT NOT NULL
	);
	`)
	if err != nil {
		log.Fatal(err)
	}

	var exportBucket func(*bolt.Bucket, int64) error

	exportBucket = func(b *bolt.Bucket, parentID int64) error {
		return b.ForEach(func(k, v []byte) error {
			if v == nil {
				result, err := dst.Exec(
					"INSERT INTO buckets(parent_id, name) VALUES(?, ?)",
					parentID, string(k),
				)
				if err != nil {
					return err
				}

				id, err := result.LastInsertId()
				if err != nil {
					return err
				}

				return exportBucket(b.Bucket(k), id)
			}

			valueType := "BLOB"
			var valueText any
			var valueBlob any = v

			if isText(v) {
				valueType = "TEXT"
				valueText = string(v)
				valueBlob = nil
			}

			_, err := dst.Exec(`
				INSERT INTO records
				(bucket_id, key_hex, key_text, value_text, value_blob, value_type)
				VALUES (?, ?, ?, ?, ?, ?)
			`,
				parentID,
				hex.EncodeToString(k),
				string(k),
				valueText,
				valueBlob,
				valueType,
			)

			return err
		})
	}

	err = src.View(func(tx *bolt.Tx) error {
		return tx.ForEach(func(name []byte, b *bolt.Bucket) error {
			result, err := dst.Exec(
				"INSERT INTO buckets(parent_id, name) VALUES(NULL, ?)",
				string(name),
			)
			if err != nil {
				return err
			}

			id, err := result.LastInsertId()
			if err != nil {
				return err
			}

			return exportBucket(b, id)
		})
	})

	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("Export berhasil:", output)
}

func isText(data []byte) bool {
	for _, b := range data {
		if b == 0 {
			return false
		}
	}
	return true
}
