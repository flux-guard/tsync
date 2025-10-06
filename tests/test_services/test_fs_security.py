"""
Тесты безопасности для FileSystemService.
"""
import pytest
from pathlib import Path
import tempfile

from tsync.services.fs import FileSystemService, FileSystemError


@pytest.fixture
def fs_service():
    """Создает экземпляр FileSystemService."""
    return FileSystemService()


@pytest.fixture
def temp_project_dir():
    """Создает временную директорию проекта."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestPathTraversalProtection:
    """Тесты защиты от path traversal атак."""

    def test_validate_path_within_directory_valid(self, fs_service, temp_project_dir):
        """Валидный путь внутри проекта проходит проверку."""
        valid_path = temp_project_dir / "subdir" / "file.txt"

        # Не должно быть исключения
        fs_service.validate_path_within_directory(valid_path, temp_project_dir)

    def test_validate_path_within_directory_traversal_attack(self, fs_service, temp_project_dir):
        """Попытка path traversal блокируется."""
        malicious_path = temp_project_dir / ".." / ".." / "etc" / "passwd"

        with pytest.raises(FileSystemError) as exc_info:
            fs_service.validate_path_within_directory(malicious_path, temp_project_dir)

        assert "выходит за пределы" in str(exc_info.value)
        assert "path traversal" in str(exc_info.value).lower()

    def test_validate_path_absolute_outside(self, fs_service, temp_project_dir):
        """Абсолютный путь вне проекта блокируется."""
        outside_path = Path("/etc/passwd")

        with pytest.raises(FileSystemError) as exc_info:
            fs_service.validate_path_within_directory(outside_path, temp_project_dir)

        assert "выходит за пределы" in str(exc_info.value)

    def test_validate_path_with_symlink_escape(self, fs_service, temp_project_dir):
        """Попытка выйти через symlink блокируется."""
        # Создаем symlink который указывает наружу
        outside_dir = temp_project_dir.parent / "outside"
        outside_dir.mkdir(exist_ok=True)

        symlink_path = temp_project_dir / "escape_link"
        try:
            symlink_path.symlink_to(outside_dir)
            malicious_path = symlink_path / "file.txt"

            with pytest.raises(FileSystemError):
                fs_service.validate_path_within_directory(malicious_path, temp_project_dir)
        finally:
            if symlink_path.exists():
                symlink_path.unlink()
            if outside_dir.exists():
                outside_dir.rmdir()

    def test_validate_path_edge_case_same_directory(self, fs_service, temp_project_dir):
        """Путь равный base_dir проходит проверку."""
        # Не должно быть исключения
        fs_service.validate_path_within_directory(temp_project_dir, temp_project_dir)


class TestFileOperations:
    """Тесты файловых операций."""

    def test_write_file_creates_parent_dirs(self, fs_service, temp_project_dir):
        """write_file создает родительские директории."""
        nested_file = temp_project_dir / "a" / "b" / "c" / "file.txt"
        content = "test content"

        fs_service.write_file(nested_file, content)

        assert nested_file.exists()
        assert nested_file.read_text(encoding="utf-8") == content

    def test_copy_file_nonexistent_source(self, fs_service, temp_project_dir):
        """copy_file выбрасывает ошибку при отсутствующем источнике."""
        source = temp_project_dir / "nonexistent.txt"
        dest = temp_project_dir / "dest.txt"

        with pytest.raises(FileSystemError) as exc_info:
            fs_service.copy_file(source, dest)

        assert "не существует" in str(exc_info.value)

    def test_read_yaml_empty_file(self, fs_service, temp_project_dir):
        """read_yaml выбрасывает ошибку для пустого файла."""
        empty_file = temp_project_dir / "empty.yml"
        empty_file.write_text("", encoding="utf-8")

        with pytest.raises(FileSystemError) as exc_info:
            fs_service.read_yaml(empty_file)

        assert "Пустой или невалидный" in str(exc_info.value)

    def test_read_yaml_invalid_syntax(self, fs_service, temp_project_dir):
        """read_yaml выбрасывает ошибку для невалидного YAML."""
        invalid_file = temp_project_dir / "invalid.yml"
        invalid_file.write_text("key: [invalid yaml", encoding="utf-8")

        with pytest.raises(FileSystemError) as exc_info:
            fs_service.read_yaml(invalid_file)

        assert "Невалидный YAML" in str(exc_info.value)
