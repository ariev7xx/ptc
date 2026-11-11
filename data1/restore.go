
package main

import (
	"database/sql"
	"encoding/hex"
	"fmt"
	"log"

	bolt "go.etcd.io/bbolt"
	_ "modernc.org/sqlite"
)

func main() {
	src, err := sql.Open("sqlite", "psiphon.db")
	if err != nil {
		log.Fatal(err)
	}
	defer src.Close()

	dst, err := bolt.Open("psiphon.boltdb", 0600, nil)
	if err != nil {
		log.Fatal(err)
	}
	defer dst.Close()

	err = dst.Update(func(tx *bolt.Tx) error {
		rows, err := src.Query(`
			SELECT id, parent_id, name
			FROM buckets ORDER BY id
		`)
		if err != nil {
			return err
		}
		defer rows.Close()

		type BucketInfo struct {
			ID       int64
			ParentID sql.NullInt64
			Name     string
		}

		var buckets []BucketInfo

		for rows.Next() {
			var b BucketInfo
			if err := rows.Scan(&b.ID, &b.ParentID, &b.Name); err != nil {
				return err
			}
			buckets = append(buckets, b)
		}
		if err := rows.Err(); err != nil {
			return err
		}

		created := make(map[int64]*bolt.Bucket)

		for _, b := range buckets {
			var parent *bolt.Bucket

			if b.ParentID.Valid {
				parent = created[b.ParentID.Int64]
				if parent == nil {
					return fmt.Errorf("parent bucket %d belum tersedia", b.ParentID.Int64)
				}
			}

			var bucket *bolt.Bucket

			if parent == nil {
				bucket, err = tx.CreateBucketIfNotExists([]byte(b.Name))
			} else {
				bucket, err = parent.CreateBucketIfNotExists([]byte(b.Name))
			}

			if err != nil {
				return err
			}

			created[b.ID] = bucket
		}

		for _, b := range buckets {
			bucket := created[b.ID]

			rows, err := src.Query(`
				SELECT key_hex, value_text, value_blob, value_type
				FROM records WHERE bucket_id = ?
			`, b.ID)
			if err != nil {
				return err
			}

			for rows.Next() {
				var keyHex, valueType string
				var valueText, valueBlob sql.NullString

				if err := rows.Scan(
					&keyHex, &valueText, &valueBlob, &valueType,
				); err != nil {
					rows.Close()
					return err
				}

				key, err := hex.DecodeString(keyHex)
				if err != nil {
					rows.Close()
					return err
				}

				var value []byte

				if valueType == "TEXT" {
					value = []byte(valueText.String)
				} else {
					value = []byte(valueBlob.String)
				}

				if err := bucket.Put(key, value); err != nil {
					rows.Close()
					return err
				}
			}

			if err := rows.Err(); err != nil {
				rows.Close()
				return err
			}
			rows.Close()
		}

		return nil
	})

	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("Berhasil: psiphon.boltdb")
}
