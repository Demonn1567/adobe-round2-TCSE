import Select from "react-select";

export default function VoiceSelect({ narrate, voice, setVoice, voices = [] }) {
  const opts =
    Array.isArray(voices) && voices.length
      ? voices.map((v) => {
          const val = v.shortName || v.name;
          const label = `${v.shortName || v.name}${v.locale ? ` (${v.locale})` : ""}`;
          return { value: val, label };
        })
      : [{ value: "", label: "Loading voices…" }];

  const customStyles = {
    control: (base, state) => ({
      ...base,
      backgroundColor: "rgb(21,33,53)",
      fontFamily: "var(--ff-component-content)",
      border: "0px",
      opacity: narrate ? 1 : 0.5,
      boxShadow: state.isFocused ? "0 0 0 2px #4c9aff" : "none",
      "&:hover": { borderColor: "#4c9aff" },
      borderRadius: "1rem",
      padding: "0 0.5rem",
      fontSize: "var(--font-size-base)",
      minWidth: 190,
    }),
    menu: (base) => ({
      ...base,
      backgroundColor: "rgb(30,45,70)",
      borderRadius: 8,
      marginTop: 0,
      overflow: "hidden",
    }),
    option: (base, state) => ({
      ...base,
      backgroundColor: state.isFocused ? "rgb(50,75,110)" : "rgb(30,45,70)",
      color: "white",
      cursor: "pointer",
      fontFamily: "var(--ff-component-content)",
      fontSize: "var(--font-size-base)",
    }),
    singleValue: (base) => ({ ...base, color: "white" }),
    placeholder: (base) => ({ ...base, color: "rgb(160, 170, 190)" }),
    dropdownIndicator: (base) => ({
      ...base,
      color: "white",
      "&:hover": { color: "#4c9aff" },
    }),
    menuList: (base) => ({ ...base, backgroundColor: "rgb(30,45,70)" }),
  };

  return (
    <Select
      isDisabled={!narrate}
      value={opts.find((o) => o.value === voice) || null}
      onChange={(sel) => setVoice(sel?.value || "")}
      options={opts}
      styles={customStyles}
      placeholder="Select voice"
      title="Voice"
    />
  );
}
