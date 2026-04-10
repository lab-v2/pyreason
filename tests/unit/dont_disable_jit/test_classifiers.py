from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import torch
import torch.nn as nn

from pyreason.scripts.learning.classification.classifier import LogicIntegratedClassifier
from pyreason.scripts.learning.classification.hf_classifier import HuggingFaceLogicIntegratedClassifier
from pyreason.scripts.learning.classification.logic_integration_base import LogicIntegrationBase
from pyreason.scripts.learning.classification.temporal_classifier import TemporalLogicIntegratedClassifier
from pyreason.scripts.learning.utils.model_interface import ModelInterfaceOptions


class TestLogicIntegrationBase:
    """Test that the abstract base class enforces the expected contract."""

    def test_cannot_instantiate_directly(self):
        model = nn.Linear(4, 2)
        opts = ModelInterfaceOptions()
        with pytest.raises(TypeError):
            LogicIntegrationBase(model, ["a", "b"], opts, "test")

    def test_subclass_must_implement_abstract_methods(self):
        class Incomplete(LogicIntegrationBase):
            pass

        model = nn.Linear(4, 2)
        opts = ModelInterfaceOptions()
        with pytest.raises(TypeError):
            Incomplete(model, ["a", "b"], opts, "test")


class TestLogicIntegratedClassifier:
    """Basic coverage for the standard multi-class classifier wrapper."""

    @pytest.fixture
    def default_opts(self):
        return ModelInterfaceOptions(
            threshold=0.5,
            set_lower_bound=True,
            set_upper_bound=False,
            snap_value=1.0
        )

    @pytest.fixture
    def classifier(self, default_opts):
        torch.manual_seed(0)
        model = nn.Linear(4, 3)
        return LogicIntegratedClassifier(
            model,
            class_names=["cat", "dog", "bird"],
            identifier="test_clf",
            interface_options=default_opts
        )

    def test_forward_returns_three_tuple(self, classifier):
        x = torch.rand(1, 4)
        result = classifier(x)
        assert len(result) == 3

    def test_forward_returns_logits_probs_facts(self, classifier):
        x = torch.rand(1, 4)
        logits, probs, facts = classifier(x)
        assert logits.shape == (1, 3)
        assert probs.shape == (1, 3)
        assert isinstance(facts, list)

    def test_probabilities_sum_to_one(self, classifier):
        x = torch.rand(1, 4)
        _, probs, _ = classifier(x)
        assert abs(probs.sum().item() - 1.0) < 1e-5

    def test_produces_one_fact_per_class(self, classifier):
        x = torch.rand(1, 4)
        _, _, facts = classifier(x)
        assert len(facts) == 3

    def test_fact_names_contain_identifier(self, classifier):
        x = torch.rand(1, 4)
        _, _, facts = classifier(x)
        for fact in facts:
            assert "test_clf" in fact.name

    def test_fact_predicates_match_class_names(self, classifier):
        x = torch.rand(1, 4)
        _, _, facts = classifier(x)
        pred_names = [str(f.pred) for f in facts]
        assert set(pred_names) == {"cat", "dog", "bird"}

    def test_batch_input_produces_n_times_c_facts(self, classifier):
        x = torch.rand(3, 4)
        _, _, facts = classifier(x)
        assert len(facts) == 9  # 3 samples * 3 classes

    def test_snap_value_bounds(self, default_opts):
        """When a probability exceeds threshold, lower bound should snap to snap_value."""
        torch.manual_seed(42)
        # Use a model that outputs a clear winner
        model = nn.Linear(2, 2)
        clf = LogicIntegratedClassifier(
            model, ["yes", "no"], identifier="snap_test",
            interface_options=default_opts
        )
        # Feed input that produces a high probability for one class
        x = torch.tensor([[10.0, -10.0]])
        _, probs, facts = clf(x)
        # The dominant class should have lower=1.0 (snapped), upper=1.0 (default)
        dominant_fact = [f for f in facts if f.bound.lower == 1.0][0]
        assert dominant_fact.bound.lower == 1.0
        assert dominant_fact.bound.upper == 1.0

    def test_no_snap_value_uses_raw_probabilities(self):
        """When snap_value is None, bounds should use the raw probability."""
        opts = ModelInterfaceOptions(
            threshold=0.0,
            set_lower_bound=True,
            set_upper_bound=True,
            snap_value=None
        )
        torch.manual_seed(0)
        model = nn.Linear(2, 2)
        clf = LogicIntegratedClassifier(
            model, ["a", "b"], identifier="raw_test",
            interface_options=opts
        )
        x = torch.rand(1, 2)
        _, probs, facts = clf(x)
        # With threshold=0 and snap_value=None, bounds should equal raw probabilities
        for i, fact in enumerate(facts):
            expected = probs[0, i].item()
            assert abs(fact.bound.lower - expected) < 1e-3
            assert abs(fact.bound.upper - expected) < 1e-3

    def test_below_threshold_gets_default_bounds(self, default_opts):
        """Classes below threshold should get [0, 1] bounds."""
        torch.manual_seed(0)
        model = nn.Linear(2, 2)
        clf = LogicIntegratedClassifier(
            model, ["a", "b"], identifier="thresh_test",
            interface_options=default_opts
        )
        x = torch.tensor([[10.0, -10.0]])
        _, probs, facts = clf(x)
        # The losing class (prob ≈ 0) should have [0, 1]
        losing = [f for f in facts if f.bound.lower == 0.0 and f.bound.upper == 1.0]
        assert len(losing) == 1

    def test_time_bounds_propagate(self, classifier):
        x = torch.rand(1, 4)
        _, _, facts = classifier(x, t1=5, t2=10)
        for fact in facts:
            assert fact.start_time == 5
            assert fact.end_time == 10

    def test_logits_shape_mismatch_raises(self):
        """Passing wrong input dimension should raise ValueError from _postprocess."""
        opts = ModelInterfaceOptions()
        model = nn.Linear(4, 3)
        clf = LogicIntegratedClassifier(
            model, ["a", "b"], identifier="bad",
            interface_options=opts
        )
        x = torch.rand(1, 4)  # model outputs 3 but class_names has 2
        with pytest.raises(ValueError, match="Expected logits of shape"):
            clf(x)

    def test_class_names_not_mutated(self, classifier):
        original = list(classifier.class_names)
        x = torch.rand(1, 4)
        classifier(x)
        classifier(x)
        assert classifier.class_names == original


def _make_hf_mock_model(num_classes=5):
    """Create a mock HuggingFace model that returns logits from a Linear layer."""
    linear = nn.Linear(10, num_classes)
    id2label = {
        0: "goldfish, Carassius auratus",
        1: "tiger shark, Galeocerdo cuvieri",
        2: "hammerhead, hammerhead shark",
        3: "great white shark, white shark",
        4: "tench, Tinca tinca",
    }

    def mock_forward(**kwargs):
        # Accept any kwargs (like pixel_values), return logits from the linear layer
        x = torch.rand(1, 10)
        return SimpleNamespace(logits=linear(x))

    model = MagicMock()
    model.side_effect = mock_forward
    model.config = SimpleNamespace(id2label=id2label)
    # Make it pass isinstance checks for nn.Module by giving it the needed attrs
    model.training = False
    return model


class TestHuggingFaceClassifier:
    """Basic coverage for the HuggingFace classifier wrapper using mocked models."""

    @pytest.fixture
    def default_opts(self):
        return ModelInterfaceOptions(
            threshold=0.5,
            set_lower_bound=True,
            set_upper_bound=False,
            snap_value=1.0
        )

    @pytest.fixture
    def hf_classifier(self, default_opts):
        torch.manual_seed(0)
        model = _make_hf_mock_model()
        return HuggingFaceLogicIntegratedClassifier(
            model,
            class_names=["goldfish", "tiger shark", "hammerhead", "great white shark", "tench"],
            identifier="hf_test",
            interface_options=default_opts,
            limit_classes=False
        )

    @pytest.fixture
    def hf_classifier_limited(self, default_opts):
        torch.manual_seed(0)
        model = _make_hf_mock_model()
        return HuggingFaceLogicIntegratedClassifier(
            model,
            class_names=["goldfish", "tiger shark", "hammerhead", "great white shark", "tench"],
            identifier="hf_limited",
            interface_options=default_opts,
            limit_classes=True
        )

    def test_forward_returns_three_tuple(self, hf_classifier):
        inputs = {"pixel_values": torch.rand(1, 3, 224, 224)}
        result = hf_classifier(inputs)
        assert len(result) == 3

    def test_produces_facts(self, hf_classifier):
        inputs = {"pixel_values": torch.rand(1, 3, 224, 224)}
        _, _, facts = hf_classifier(inputs)
        assert len(facts) > 0

    def test_fact_names_contain_identifier(self, hf_classifier):
        inputs = {"pixel_values": torch.rand(1, 3, 224, 224)}
        _, _, facts = hf_classifier(inputs)
        for fact in facts:
            assert "hf_test" in fact.name

    def test_time_bounds_propagate(self, hf_classifier):
        inputs = {"pixel_values": torch.rand(1, 3, 224, 224)}
        _, _, facts = hf_classifier(inputs, t1=3, t2=7)
        for fact in facts:
            assert fact.start_time == 3
            assert fact.end_time == 7

    def test_limit_classes_produces_correct_count(self, hf_classifier_limited):
        inputs = {"pixel_values": torch.rand(1, 3, 224, 224)}
        _, _, facts = hf_classifier_limited(inputs)
        assert len(facts) == 5

    def test_limit_classes_does_not_mutate_class_names(self, hf_classifier_limited):
        original = list(hf_classifier_limited.class_names)
        inputs = {"pixel_values": torch.rand(1, 3, 224, 224)}
        hf_classifier_limited(inputs)
        hf_classifier_limited(inputs)
        assert hf_classifier_limited.class_names == original

    def test_limit_classes_facts_use_filtered_labels(self, hf_classifier_limited):
        inputs = {"pixel_values": torch.rand(1, 3, 224, 224)}
        _, _, facts = hf_classifier_limited(inputs)
        # All fact predicates should be real label names from id2label, not indices
        for fact in facts:
            pred = str(fact.pred)
            assert pred.replace(" ", "").isalpha() or " " in pred


def _make_yolo_mock_model(label_name="dog", confidence=0.85):
    """Create a mock YOLO model that returns a single detection."""
    mock_box = MagicMock()
    mock_box.cls = torch.tensor([1])
    mock_box.conf = torch.tensor([confidence])

    mock_result = MagicMock()
    mock_result.boxes = [mock_box]
    mock_result.names = {0: "cat", 1: label_name, 2: "bird"}

    model = MagicMock()
    model.predict.return_value = [mock_result]
    model.training = False
    return model


class TestYoloClassifier:
    """Basic coverage for the YOLO classifier wrapper using mocked models."""

    @pytest.fixture
    def default_opts(self):
        return ModelInterfaceOptions(
            threshold=0.5,
            set_lower_bound=True,
            set_upper_bound=False,
            snap_value=1.0
        )

    @pytest.fixture
    def yolo_classifier(self, default_opts):
        from pyreason.scripts.learning.classification.yolo_classifier import (
            YoloLogicIntegratedTemporalClassifier,
        )
        model = _make_yolo_mock_model("dog", 0.85)
        return YoloLogicIntegratedTemporalClassifier(
            model,
            class_names=["cat", "dog", "bird"],
            identifier="yolo_test",
            interface_options=default_opts,
            poll_interval=None,  # disable polling for unit tests
        )

    def test_forward_returns_three_tuple(self, yolo_classifier):
        raw, postproc, facts = yolo_classifier("fake_image.jpg")
        assert len((raw, postproc, facts)) == 3

    def test_produces_single_fact(self, yolo_classifier):
        _, _, facts = yolo_classifier("fake_image.jpg")
        assert len(facts) == 1

    def test_fact_contains_detected_label(self, yolo_classifier):
        _, _, facts = yolo_classifier("fake_image.jpg")
        assert "dog" in str(facts[0].pred)

    def test_fact_name_contains_identifier(self, yolo_classifier):
        _, _, facts = yolo_classifier("fake_image.jpg")
        assert "yolo_test" in facts[0].name

    def test_postprocess_returns_label_and_confidence(self, yolo_classifier):
        _, postproc, _ = yolo_classifier("fake_image.jpg")
        assert postproc[0] == "dog"
        assert abs(postproc[1] - 0.85) < 1e-2

    def test_snap_value_applied(self, yolo_classifier):
        _, _, facts = yolo_classifier("fake_image.jpg")
        # snap_value=1.0 with set_lower_bound=True → lower should be 1.0
        assert facts[0].bound.lower == 1.0

    def test_time_bounds_propagate(self, yolo_classifier):
        _, _, facts = yolo_classifier("fake_image.jpg", t1=2, t2=5)
        assert facts[0].start_time == 2
        assert facts[0].end_time == 5

    def test_no_snap_uses_confidence(self):
        from pyreason.scripts.learning.classification.yolo_classifier import (
            YoloLogicIntegratedTemporalClassifier,
        )
        opts = ModelInterfaceOptions(
            threshold=0.5,
            set_lower_bound=True,
            set_upper_bound=True,
            snap_value=None
        )
        model = _make_yolo_mock_model("cat", 0.92)
        clf = YoloLogicIntegratedTemporalClassifier(
            model, ["cat", "dog"], identifier="nosnap",
            interface_options=opts, poll_interval=None
        )
        _, _, facts = clf("img.jpg")
        assert abs(facts[0].bound.lower - 0.92) < 1e-2
        assert abs(facts[0].bound.upper - 0.92) < 1e-2

    def test_no_polling_thread_when_interval_none(self, yolo_classifier):
        # poll_interval=None means no background thread should be started
        # Verify the classifier works normally without hanging
        _, _, facts = yolo_classifier("test.jpg")
        assert len(facts) == 1


class TestTemporalLogicIntegratedClassifier:
    """Basic coverage for the temporal classifier wrapper (no polling)."""

    @pytest.fixture
    def default_opts(self):
        return ModelInterfaceOptions(
            threshold=0.5,
            set_lower_bound=True,
            set_upper_bound=False,
            snap_value=1.0
        )

    @pytest.fixture
    def temporal_classifier(self, default_opts):
        torch.manual_seed(0)
        model = nn.Linear(4, 3)
        return TemporalLogicIntegratedClassifier(
            model,
            class_names=["cat", "dog", "bird"],
            identifier="temporal_test",
            interface_options=default_opts,
            poll_interval=None,  # disable polling for unit tests
        )

    def test_forward_returns_three_tuple(self, temporal_classifier):
        x = torch.rand(1, 4)
        result = temporal_classifier(x)
        assert len(result) == 3

    def test_forward_returns_logits_probs_facts(self, temporal_classifier):
        x = torch.rand(1, 4)
        logits, probs, facts = temporal_classifier(x)
        assert logits.shape == (1, 3)
        assert probs.shape == (1, 3)
        assert isinstance(facts, list)

    def test_probabilities_sum_to_one(self, temporal_classifier):
        x = torch.rand(1, 4)
        _, probs, _ = temporal_classifier(x)
        assert abs(probs.sum().item() - 1.0) < 1e-5

    def test_produces_one_fact_per_class(self, temporal_classifier):
        x = torch.rand(1, 4)
        _, _, facts = temporal_classifier(x)
        assert len(facts) == 3

    def test_fact_names_contain_identifier(self, temporal_classifier):
        x = torch.rand(1, 4)
        _, _, facts = temporal_classifier(x)
        for fact in facts:
            assert "temporal_test" in fact.name

    def test_fact_predicates_match_class_names(self, temporal_classifier):
        x = torch.rand(1, 4)
        _, _, facts = temporal_classifier(x)
        pred_names = [str(f.pred) for f in facts]
        assert set(pred_names) == {"cat", "dog", "bird"}

    def test_batch_input_produces_n_times_c_facts(self, temporal_classifier):
        x = torch.rand(3, 4)
        _, _, facts = temporal_classifier(x)
        assert len(facts) == 9  # 3 samples * 3 classes

    def test_time_bounds_propagate(self, temporal_classifier):
        x = torch.rand(1, 4)
        _, _, facts = temporal_classifier(x, t1=5, t2=10)
        for fact in facts:
            assert fact.start_time == 5
            assert fact.end_time == 10

    def test_logits_shape_mismatch_raises(self):
        opts = ModelInterfaceOptions()
        model = nn.Linear(4, 3)
        clf = TemporalLogicIntegratedClassifier(
            model, ["a", "b"], identifier="bad",
            interface_options=opts, poll_interval=None
        )
        x = torch.rand(1, 4)  # model outputs 3 but class_names has 2
        with pytest.raises(ValueError, match="Expected logits of shape"):
            clf(x)

    def test_get_class_facts(self, temporal_classifier):
        facts = temporal_classifier.get_class_facts(t1=0, t2=5)
        assert len(facts) == 3
        for fact in facts:
            assert fact.start_time == 0
            assert fact.end_time == 5
            assert fact.bound.lower == 1.0
            assert fact.bound.upper == 1.0

    def test_no_polling_thread_when_interval_none(self, temporal_classifier):
        # Just verify it works without hanging
        x = torch.rand(1, 4)
        _, _, facts = temporal_classifier(x)
        assert len(facts) == 3
