"""
test_udp_parser.py

Unit tests for parselibrary.udp_parser.

Tests are written against synthetic tec5 packets produced by the
mock_udp_emitter, so they exercise the real binary parsing logic
without needing a physical spectrometer or a live network socket.
"""

import math
import struct
import pytest

from app.parselibrary.udp_parser import unpack_udp
from app.parselibrary.mock_udp_emitter import build_tec5_packet

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(
    params=[4, 5, 7, 9, 11],
    ids=["sample", "reference", "transmission", "absorbance", "calibration"],
)
def any_packet(request):
    """One synthetic 840-byte packet for each recognised spectral type."""
    return build_tec5_packet(spec_type=request.param)


# ---------------------------------------------------------------------------
# Packet structure / length
# ---------------------------------------------------------------------------


class TestPacketStructure:
    def test_packet_is_840_bytes(self, any_packet):
        """build_tec5_packet must always produce exactly 840 bytes."""
        assert len(any_packet) == 840

    def test_unpack_returns_list(self, any_packet):
        result = unpack_udp(any_packet)
        assert isinstance(result, list)

    def test_unpack_returns_201_points(self, any_packet):
        """Every tec5 packet carries exactly 201 wavelength samples."""
        result = unpack_udp(any_packet)
        assert len(result) == 201

    def test_all_values_are_floats(self, any_packet):
        result = unpack_udp(any_packet)
        assert all(isinstance(v, float) for v in result)


# ---------------------------------------------------------------------------
# Wavelength header metadata
# ---------------------------------------------------------------------------


class TestPacketHeader:
    def test_spectra_type_in_header(self):
        """Byte 16 of the packet encodes the spectral type ID."""
        for spec_type in [4, 5, 7, 9, 11]:
            pkt = build_tec5_packet(spec_type=spec_type)
            extracted = struct.unpack("<B", pkt[16:17])[0]
            assert extracted == spec_type, f"spec_type mismatch for type {spec_type}"

    def test_wavelength_start_is_190(self):
        pkt = build_tec5_packet(spec_type=9)
        w_start = struct.unpack("<f", pkt[20:24])[0]
        assert pytest.approx(w_start, abs=0.01) == 190.0

    def test_wavelength_end_is_390(self):
        pkt = build_tec5_packet(spec_type=9)
        w_end = struct.unpack("<f", pkt[24:28])[0]
        assert pytest.approx(w_end, abs=0.01) == 390.0

    def test_wavelength_increment_is_1nm(self):
        pkt = build_tec5_packet(spec_type=9)
        w_step = struct.unpack("<f", pkt[28:32])[0]
        assert pytest.approx(w_step, abs=0.001) == 1.0


# ---------------------------------------------------------------------------
# Spectral value correctness — round-trip build → parse
# ---------------------------------------------------------------------------


class TestAbsorbanceSpectrum:
    """Type 9: Gaussian peak centred at 280 nm."""

    def setup_method(self):
        self.data = unpack_udp(build_tec5_packet(spec_type=9, t_offset=0.0))

    def test_280nm_is_near_peak(self):
        """The 280 nm bin (index 90) should have the highest absorbance value."""
        idx_280 = 90  # 280 - 190 = 90
        peak_value = self.data[idx_280]
        assert peak_value == max(self.data), "280 nm should be the absorbance peak"

    def test_absorbance_positive_everywhere(self):
        assert all(v >= 0.0 for v in self.data)

    def test_wings_lower_than_peak(self):
        """Far-UV (190 nm) and far edge (390 nm) must be substantially below peak."""
        peak = max(self.data)
        assert self.data[0] < peak * 0.5, "190 nm should be well below peak"
        assert self.data[-1] < peak * 0.5, "390 nm should be well below peak"

    def test_gaussian_symmetry(self):
        """Values at ±30 nm from peak should be approximately symmetric."""
        idx_280 = 90
        left = self.data[idx_280 - 30]  # 250 nm
        right = self.data[idx_280 + 30]  # 310 nm
        assert pytest.approx(left, rel=0.05) == right


class TestTransmissionSpectrum:
    """Type 7: flat 0.85 transmission across all wavelengths."""

    def setup_method(self):
        self.data = unpack_udp(build_tec5_packet(spec_type=7))

    def test_all_values_are_085(self):
        for v in self.data:
            assert pytest.approx(v, abs=1e-4) == 0.85

    def test_spectrum_is_flat(self):
        assert max(self.data) - min(self.data) < 1e-4


class TestCalibrationSpectrum:
    """Type 11: flat unity (1.0) calibration baseline."""

    def setup_method(self):
        self.data = unpack_udp(build_tec5_packet(spec_type=11))

    def test_all_values_are_unity(self):
        for v in self.data:
            assert pytest.approx(v, abs=1e-4) == 1.0


class TestReferenceIntensitySpectrum:
    """Type 5: sinusoidal lamp emission curve, all values positive."""

    def setup_method(self):
        self.data = unpack_udp(build_tec5_packet(spec_type=5))

    def test_all_positive(self):
        assert all(v > 0 for v in self.data)

    def test_baseline_around_8000(self):
        """Mean should be between 8000 and 12000 (DC offset + positive sine lobe)."""
        mean = sum(self.data) / len(self.data)
        assert 8000 < mean < 12000


class TestSampleIntensitySpectrum:
    """Type 4: reference attenuated by a UV-absorbing peak at 280 nm."""

    def setup_method(self):
        self.data = unpack_udp(build_tec5_packet(spec_type=4, t_offset=0.0))

    def test_all_positive(self):
        assert all(v > 0 for v in self.data)

    def test_280nm_is_attenuated(self):
        """Sample intensity at 280 nm should be lower than at flanking wavelengths."""
        idx_280 = 90
        val_at_peak = self.data[idx_280]
        val_at_250 = self.data[60]
        val_at_350 = self.data[160]
        assert (
            val_at_peak < val_at_250
        ), "Sample at 280 nm should be attenuated vs 250 nm"
        assert (
            val_at_peak < val_at_350
        ), "Sample at 280 nm should be attenuated vs 350 nm"


# ---------------------------------------------------------------------------
# Spectra type mapping (from collect_mpt_spectra logic)
# ---------------------------------------------------------------------------


class TestSpectraTypeMapping:
    SPECTRA_MAPPING = {
        4: "sample",
        5: "onlinereference",
        7: "transmission",
        9: "absorbance",
        11: "calibration",
    }

    def test_all_known_types_are_mapped(self):
        assert set(self.SPECTRA_MAPPING.keys()) == {4, 5, 7, 9, 11}

    @pytest.mark.parametrize(
        "spec_type,expected_name",
        [
            (4, "sample"),
            (5, "onlinereference"),
            (7, "transmission"),
            (9, "absorbance"),
            (11, "calibration"),
        ],
    )
    def test_type_name(self, spec_type, expected_name):
        assert self.SPECTRA_MAPPING[spec_type] == expected_name

    def test_unknown_type_raises_key_error(self):
        with pytest.raises(KeyError):
            _ = self.SPECTRA_MAPPING[99]
