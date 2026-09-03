"""
test_mock_emitter.py

Unit tests for parselibrary.mock_udp_emitter.build_tec5_packet.

Validates the emitter independently of the parser so that failures
in either can be isolated.
"""

import struct
import pytest

from app.parselibrary.mock_udp_emitter import build_tec5_packet

ALL_SPEC_TYPES = [4, 5, 7, 9, 11]


# ---------------------------------------------------------------------------
# Packet construction
# ---------------------------------------------------------------------------


class TestBuildTec5Packet:
    @pytest.mark.parametrize("spec_type", ALL_SPEC_TYPES)
    def test_packet_length_is_840(self, spec_type):
        """tec5 protocol requires exactly 840 bytes per datagram."""
        pkt = build_tec5_packet(spec_type=spec_type)
        assert (
            len(pkt) == 840
        ), f"Expected 840 bytes, got {len(pkt)} for type {spec_type}"

    @pytest.mark.parametrize("spec_type", ALL_SPEC_TYPES)
    def test_packet_is_bytes(self, spec_type):
        pkt = build_tec5_packet(spec_type=spec_type)
        assert isinstance(pkt, bytes)

    def test_header_is_36_bytes(self):
        """Header format '<4sIIHHHHfffI' always packs to 36 bytes."""
        pkt = build_tec5_packet(spec_type=9)
        header_size = struct.calcsize("<4sIIHHHHfffI")
        assert header_size == 36

    def test_payload_length_field(self):
        """Bytes 8-11 store payload_len = 840 as a little-endian uint32."""
        pkt = build_tec5_packet(spec_type=9)
        length_field = struct.unpack("<I", pkt[8:12])[0]
        assert length_field == 840

    @pytest.mark.parametrize("spec_type", ALL_SPEC_TYPES)
    def test_spec_type_encoded_at_byte_16(self, spec_type):
        """Byte 16 must contain the spectral type identifier."""
        pkt = build_tec5_packet(spec_type=spec_type)
        extracted = struct.unpack("<B", pkt[16:17])[0]
        assert extracted == spec_type

    @pytest.mark.parametrize("channel", [1, 2])
    def test_channel_encoded_at_byte_18(self, channel):
        """Bytes 18-19 encode channel index in the lower byte."""
        pkt = build_tec5_packet(spec_type=9, channel=channel)
        raw = struct.unpack("<H", pkt[18:20])[0]
        encoded_channel = raw & 0xFF
        assert encoded_channel == channel

    def test_num_pts_field_is_201(self):
        """Bytes 32-33 (first uint16 of a 2-uint16 field) must be 201."""
        pkt = build_tec5_packet(spec_type=9)
        num_pts = struct.unpack("<2H", pkt[32:36])[0]
        assert num_pts == 201

    def test_data_region_is_804_bytes(self):
        """201 floats × 4 bytes = 804 bytes of spectral data after the 36-byte header."""
        pkt = build_tec5_packet(spec_type=9)
        data_bytes = pkt[36:]
        assert len(data_bytes) == 804

    @pytest.mark.parametrize("spec_type", ALL_SPEC_TYPES)
    def test_data_region_parseable_as_201_floats(self, spec_type):
        pkt = build_tec5_packet(spec_type=spec_type)
        values = list(struct.unpack("<201f", pkt[36:]))
        assert len(values) == 201


# ---------------------------------------------------------------------------
# Per-type value behaviour
# ---------------------------------------------------------------------------


class TestEmitterValues:
    def test_calibration_is_all_ones(self):
        pkt = build_tec5_packet(spec_type=11)
        values = list(struct.unpack("<201f", pkt[36:]))
        assert all(pytest.approx(v, abs=1e-5) == 1.0 for v in values)

    def test_transmission_is_flat_085(self):
        pkt = build_tec5_packet(spec_type=7)
        values = list(struct.unpack("<201f", pkt[36:]))
        assert all(pytest.approx(v, abs=1e-4) == 0.85 for v in values)

    def test_absorbance_peak_is_at_index_90(self):
        """Gaussian centred at 280 nm → index 90 (280 - 190 = 90)."""
        pkt = build_tec5_packet(spec_type=9, t_offset=0.0)
        values = list(struct.unpack("<201f", pkt[36:]))
        assert values.index(max(values)) == 90

    def test_reference_all_positive(self):
        pkt = build_tec5_packet(spec_type=5)
        values = list(struct.unpack("<201f", pkt[36:]))
        assert all(v > 0 for v in values)

    def test_sample_all_positive(self):
        pkt = build_tec5_packet(spec_type=4, t_offset=0.0)
        values = list(struct.unpack("<201f", pkt[36:]))
        assert all(v > 0 for v in values)

    def test_t_offset_changes_absorbance_values(self):
        """t_offset shifts the sine noise term, so values should differ."""
        pkt_t0 = build_tec5_packet(spec_type=9, t_offset=0.0)
        pkt_t1 = build_tec5_packet(spec_type=9, t_offset=1.0)
        v0 = list(struct.unpack("<201f", pkt_t0[36:]))
        v1 = list(struct.unpack("<201f", pkt_t1[36:]))
        assert (
            v0 != v1
        ), "Different t_offset values should produce different absorbance arrays"
