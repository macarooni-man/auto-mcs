package org.kivy.android;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.List;

/**
 * Exposes only individual app-managed text files with temporary intent grants.
 * The provider is not exported and cannot access Java/Telepath credentials.
 */
public class AutoMcsFiles extends ContentProvider {

    private File resolve(Uri uri) throws FileNotFoundException {
        List<String> parts = uri.getPathSegments();
        if (parts.size() < 2) throw new FileNotFoundException("Missing file path");

        File root;
        if ("shared".equals(parts.get(0))) {
            File[] media = getContext().getExternalMediaDirs();
            root = null;
            if (media != null) {
                for (File candidate : media) {
                    if (candidate != null && android.os.Environment.MEDIA_MOUNTED.equals(
                            android.os.Environment.getExternalStorageState(candidate))) {
                        root = new File(candidate, "auto-mcs");
                        break;
                    }
                }
            }
            if (root == null)
                throw new FileNotFoundException("Shared app storage unavailable");
        } else if ("temp".equals(parts.get(0))) {
            root = new File(getContext().getFilesDir(), "tmp");
        } else {
            throw new FileNotFoundException("Unsupported file root");
        }

        File file = root;
        for (int i = 1; i < parts.size(); i++) {
            String name = parts.get(i);
            if (name.isEmpty() || name.equals(".") || name.equals("..") ||
                name.indexOf('/') >= 0 || name.indexOf('\\') >= 0)
                throw new FileNotFoundException("Invalid file component");
            file = new File(file, name);
        }

        try {
            String base = root.getCanonicalPath() + File.separator;
            String target = file.getCanonicalPath();
            if (!target.startsWith(base) || !file.isFile())
                throw new FileNotFoundException("File outside shared root: " + uri);
        } catch (IOException exc) {
            throw new FileNotFoundException(exc.toString());
        }

        return file;
    }

    @Override
    public boolean onCreate() {
        return true;
    }

    @Override
    public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        File file = resolve(uri);
        if ("temp".equals(uri.getPathSegments().get(0)) && mode.contains("w"))
            throw new FileNotFoundException("Temporary files are read-only");
        return ParcelFileDescriptor.open(file, ParcelFileDescriptor.parseMode(mode));
    }

    @Override
    public String getType(Uri uri) {
        return "text/plain";
    }

    @Override
    public Cursor query(Uri uri, String[] projection, String selection,
                        String[] selectionArgs, String sortOrder) {
        File file;
        try {
            file = resolve(uri);
        } catch (FileNotFoundException exc) {
            return null;
        }
        if (projection == null) projection = new String[] {
            OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE
        };
        MatrixCursor cursor = new MatrixCursor(projection, 1);
        Object[] row = new Object[projection.length];
        for (int i = 0; i < projection.length; i++) {
            if (OpenableColumns.DISPLAY_NAME.equals(projection[i])) row[i] = file.getName();
            else if (OpenableColumns.SIZE.equals(projection[i])) row[i] = file.length();
        }
        cursor.addRow(row);
        return cursor;
    }

    @Override
    public Uri insert(Uri uri, ContentValues values) {
        throw new UnsupportedOperationException();
    }

    @Override
    public int delete(Uri uri, String selection, String[] selectionArgs) {
        throw new UnsupportedOperationException();
    }

    @Override
    public int update(Uri uri, ContentValues values, String selection, String[] selectionArgs) {
        throw new UnsupportedOperationException();
    }
}
