# Configurable PWM Generator — Tiny Tapeout

  A compact, run-time **configurable Pulse Width Modulation (PWM) generator** taped out on
  [Tiny Tapeout](https://tinytapeout.com). The design exposes live controls for the
  **period**, **duty cycle**, and **output polarity**, and ships with built-in **safety clamps**
  so it can never be driven into an unsafe or undefined state. It outputs both the PWM signal
  and its complementary (inverted) twin — ideal for driving half-bridge / push-pull style loads.

  - **Top module:** `tt_um_configurable_pwm`
  - **Technology:** gf180mcuD PDK variant (Tiny Tapeout shuttle)
  - **Area:** 1×1 tile
  - **Target clock:** 50 MHz
  - **Language:** Verilog (fully synthesizable)

  ---

  ## ✨ Features

  - 🎛️ **Run-time configurable** period (4-bit) and duty cycle (4-bit) — no resynthesis needed.
  - 🔁 **Complementary outputs** — `pwm_out` and its inverse `comp_pwm_out` generated simultaneously.
  - 🔀 **Polarity control** — a single `invert` pin flips the output logic.
  - 🛡️ **Built-in safety clamps:**
    - Period is clamped to a **minimum of 3** clock cycles (protects output pad bandwidth).
    - Duty cycle is clamped so it can **never exceed the period** (prevents overflow / glitches).
  - ⏹️ **Safe disarm** — dropping `enable` instantly forces both outputs to `0`.


  ---

  ## 🧱 Architecture

  ```
              ui_in[4:1] (period)        uio_in[3:0] (duty)
                    │                          │
                    ▼                          ▼
            ┌───────────────┐          ┌───────────────┐
            │ Period clamp  │          │  Duty clamp   │
            │  (min = 3)    │────┐     │ (≤ period)    │
            └───────────────┘    │     └───────────────┘
                    │            period        │
                    ▼             │            ▼
            ┌───────────────┐     │    ┌───────────────┐
            │  period reg   │     │    │   duty reg    │
            └───────┬───────┘     │    └───────┬───────┘
                    │             │            │
                    ▼             │            │
            ┌───────────────┐     │            │
     enable │  Up-counter   │◄────┘            │
     ─────► │  0 .. period-1│                  │
            └───────┬───────┘                  │
                    │ counter                  │
                    ▼                          ▼
                ┌─────────────────────────────────┐
                │   pwm_raw = (counter < duty)     │
                └────────────────┬────────────────┘
                                 │
                       invert ──►│ (optional polarity flip)
                                 ▼
                   uo_out[0] = pwm   (gated by enable)
                   uo_out[1] = ~pwm  (gated by enable)
  ```

  **Three core blocks:**

  1. **Input safety constraints** — combinational clamps enforce `period ≥ 3` and `duty ≤ period`
     before the values are registered.
  2. **Up-counter engine** — when enabled, an internal counter increments every clock and rolls
     over to `0` once it reaches `period − 1`.
  3. **Output generation & polarity** — `pwm_raw = (counter < duty)` is optionally inverted, then
     driven out as a complementary pair. When disabled, both outputs are held low.

  ---

  ## 📌 Pinout

  ### Inputs — `ui_in`
  | Pin        | Signal        | Description                                  |
  |------------|---------------|----------------------------------------------|
  | `ui_in[0]` | `enable`      | Enable PWM (low = both outputs forced to 0)  |
  | `ui_in[1]` | `period_in[0]`| Period value, bit 0                          |
  | `ui_in[2]` | `period_in[1]`| Period value, bit 1                          |
  | `ui_in[3]` | `period_in[2]`| Period value, bit 2                          |
  | `ui_in[4]` | `period_in[3]`| Period value, bit 3 (period = `ui_in[4:1]`)  |
  | `ui_in[5]` | `invert`      | Output polarity invert                       |
  | `ui_in[6]` | —             | Unused                                       |
  | `ui_in[7]` | —             | Unused                                       |

  ### Outputs — `uo_out`
  | Pin         | Signal          | Description                          |
  |-------------|-----------------|--------------------------------------|
  | `uo_out[0]` | `pwm_out`       | Primary PWM output                   |
  | `uo_out[1]` | `comp_pwm_out`  | Complementary (inverted) PWM output  |
  | `uo_out[7:2]`| —              | Unused (tied to 0)                   |

  ### Bidirectional — `uio` (used as inputs)
  | Pin        | Signal       | Description           |
  |------------|--------------|-----------------------|
  | `uio[0]`   | `duty_in[0]` | Duty value, bit 0     |
  | `uio[1]`   | `duty_in[1]` | Duty value, bit 1     |
  | `uio[2]`   | `duty_in[2]` | Duty value, bit 2     |
  | `uio[3]`   | `duty_in[3]` | Duty value, bit 3 (duty = `uio[3:0]`) |
  | `uio[7:4]` | —            | Unused                |

  > **Duty cycle %** ≈ `duty / period × 100`. Example: `period = 8`, `duty = 4` → 50% duty cycle.

  ---

  ## ⚙️ Behavior Reference

  | Condition                         | `pwm_out`                  | `comp_pwm_out`             |
  |-----------------------------------|----------------------------|----------------------------|
  | `enable = 0`                      | `0`                        | `0`                        |
  | `duty = 0`                        | always `0`                 | always `1`                 |
  | `duty ≥ period`                   | always `1` (100% duty)     | always `0`                 |
  | `invert = 1`                      | polarity flipped           | polarity flipped           |
  | `period < 3` requested            | clamped up to `3`          | clamped up to `3`          |
  | `duty > period` requested         | clamped down to `period`   | clamped down to `period`   |

  ---

  ## 🧪 How to Test

  The design is verified with a [cocotb](https://www.cocotb.org/) testbench (`test/test.py`) that
  exercises normal operation, the period clamp, and the disable path, asserting the outputs stay
  resolvable (no `X`/`Z`) at every step.

  ### Run the simulation locally

  ```bash
  cd test

  # RTL simulation
  make -B

  # Gate-level simulation (requires the hardened gate-level netlist)
  make -B GATES=yes
  ```

  View the resulting waveforms:

  ```bash
  gtkwave tb.vcd tb.gtkw
  ```

  ### On the Tiny Tapeout demo board

  1. **Enable** — drive `ui_in[0]` high.
  2. **Set period** — apply a value (3–15) on `ui_in[4:1]` to set the loop length.
  3. **Set duty** — apply a value on `uio[3:0]`:
     - `0` → output stays low.
     - `≥ period` → output stays high (100%).
  4. **Polarity** — drive `ui_in[5]` high to swap `pwm_out` / `comp_pwm_out`.
  5. **Disarm** — drop `ui_in[0]` low; both outputs go to `0` immediately.

  Connect the outputs to the demo board LEDs to see brightness change with duty cycle, or to a
  logic analyzer / oscilloscope to inspect the exact waveform and verify the clamps.

  ---

  ## 📁 Repository Layout

  ```
  ePWM_Tapeout/
  ├── src/
  │   ├── project.v        # tt_um_configurable_pwm — the RTL design
  │   └── config.json
  ├── test/
  │   ├── test.py          # cocotb testbench
  │   ├── tb.v             # Verilog test harness
  │   └── Makefile
  ├── docs/
  │   └── info.md          # design documentation
  ├── info.yaml            # Tiny Tapeout project + pinout metadata
  └── README.md
  ```

  ---

  ## 🚀 Build

  The GitHub Actions in this repo automatically:

  - **test** — run the cocotb RTL/GL testbench,
  - **gds** — harden the design into GDS with [LibreLane](https://www.zerotoasiccourse.com/terminology/librelane/),
  - **docs** — build the documentation page,
  - **fpga** — validate the design for FPGA.

  To build the hardened design locally, see the
  [Tiny Tapeout local hardening guide](https://www.tinytapeout.com/guides/local-hardening/).

  ---

  ## 👥 Authors

  - **Shivaranjani GR**
  - **Ganesh Ragava**
  - **Sidharth Kamalakkannan**

  ---

  ## 📜 License

  Released under the terms in [LICENSE](LICENSE).

  ---

  ## 🔗 Resources

  - [What is Tiny Tapeout?](https://tinytapeout.com)
  - [Project documentation](docs/info.md)
  - [Digital design lessons](https://tinytapeout.com/digital_design/)
  - [Tiny Tapeout FAQ](https://tinytapeout.com/faq/)
  - [Join the community](https://tinytapeout.com/discord)
