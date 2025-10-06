"""
Тесты для FileSystemService.
"""
import pytest
from pathlib import Path

from tsync.services.fs import FileSystemService, FileSystemError


class TestFileSystemService:
    """Тесты для FileSystemService."""

    def test_path_exists(self, temp_dir, fs_service):
        """Тест: проверка существования пути."""
        # Создаем тестовый файл
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        assert fs_service.path_exists(test_file) is True
        assert fs_service.path_exists(temp_dir / "nonexistent.txt") is False

    def test_ensure_dir_exists(self, temp_dir, fs_service):
        """Тест: создание родительской директории."""
        test_file = temp_dir / "subdir" / "nested" / "file.txt"
        fs_service.ensure_dir_exists(test_file)

        assert test_file.parent.exists()
        assert test_file.parent.is_dir()

    def test_read_yaml_valid(self, temp_dir, fs_service):
        """Тест: чтение валидного YAML файла."""
        yaml_file = temp_dir / "config.yaml"
        yaml_file.write_text("name: test\nversion: 1.0.0\n")

        data = fs_service.read_yaml(yaml_file)
        assert data["name"] == "test"
        assert data["version"] == "1.0.0"

    def test_read_yaml_not_found(self, temp_dir, fs_service):
        """Тест: ошибка при отсутствии YAML файла."""
        with pytest.raises(FileSystemError) as exc_info:
            fs_service.read_yaml(temp_dir / "nonexistent.yaml")
        assert "не найден" in str(exc_info.value)

    def test_read_yaml_invalid(self, temp_dir, fs_service):
        """Тест: ошибка при невалидном YAML."""
        yaml_file = temp_dir / "invalid.yaml"
        yaml_file.write_text("invalid: yaml: content:")

        with pytest.raises(FileSystemError) as exc_info:
            fs_service.read_yaml(yaml_file)
        assert "Невалидный YAML" in str(exc_info.value)

    def test_read_yaml_empty(self, temp_dir, fs_service):
        """Тест: ошибка при пустом YAML файле."""
        yaml_file = temp_dir / "empty.yaml"
        yaml_file.write_text("")

        with pytest.raises(FileSystemError) as exc_info:
            fs_service.read_yaml(yaml_file)
        assert "Пустой или невалидный" in str(exc_info.value)

    def test_read_file(self, temp_dir, fs_service):
        """Тест: чтение текстового файла."""
        test_file = temp_dir / "test.txt"
        content = "Test content\nLine 2"
        test_file.write_text(content)

        result = fs_service.read_file(test_file)
        assert result == content

    def test_read_file_not_found(self, temp_dir, fs_service):
        """Тест: ошибка при отсутствии файла."""
        with pytest.raises(FileSystemError) as exc_info:
            fs_service.read_file(temp_dir / "nonexistent.txt")
        assert "не найден" in str(exc_info.value)

    def test_write_file(self, temp_dir, fs_service):
        """Тест: запись файла."""
        test_file = temp_dir / "output.txt"
        content = "Output content"

        fs_service.write_file(test_file, content)

        assert test_file.exists()
        assert test_file.read_text() == content

    def test_write_file_creates_directories(self, temp_dir, fs_service):
        """Тест: запись файла создает родительские директории."""
        test_file = temp_dir / "sub1" / "sub2" / "output.txt"
        content = "Output content"

        fs_service.write_file(test_file, content)

        assert test_file.exists()
        assert test_file.read_text() == content

    def test_copy_file(self, temp_dir, fs_service):
        """Тест: копирование файла."""
        source = temp_dir / "source.txt"
        destination = temp_dir / "dest" / "destination.txt"
        content = "File content"

        source.write_text(content)
        fs_service.copy_file(source, destination)

        assert destination.exists()
        assert destination.read_text() == content

    def test_copy_file_source_not_found(self, temp_dir, fs_service):
        """Тест: ошибка при отсутствии исходного файла."""
        source = temp_dir / "nonexistent.txt"
        destination = temp_dir / "dest.txt"

        with pytest.raises(FileSystemError) as exc_info:
            fs_service.copy_file(source, destination)
        assert "не существует" in str(exc_info.value)

    def test_copy_binary_file(self, temp_dir, fs_service):
        """Тест: копирование бинарного файла."""
        source = temp_dir / "image.bin"
        destination = temp_dir / "image_copy.bin"
        binary_content = b"\x00\x01\x02\x03\x04"

        source.write_bytes(binary_content)
        fs_service.copy_file(source, destination)

        assert destination.exists()
        assert destination.read_bytes() == binary_content
