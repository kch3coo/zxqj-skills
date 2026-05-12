#!/bin/zsh
set -euo pipefail

usage() {
  print "Usage: zsh scan-return-codes.zsh -Root <backend-root> [-Prefix <code-prefix>] [-IncludePath <path-fragment>]"
}

normalize_code() {
  print -r -- "${1//_/}"
}

format_code() {
  local digits="$1"
  local len=${#digits}
  local result=""
  local part

  while (( len > 3 )); do
    part="${digits[-3,-1]}"
    digits="${digits[1,-4]}"
    if [[ -z "$result" ]]; then
      result="$part"
    else
      result="${part}_${result}"
    fi
    len=${#digits}
  done

  if [[ -z "$result" ]]; then
    print -r -- "$digits"
  else
    print -r -- "${digits}_${result}"
  fi
}

root=""
prefix=""
include_path=""

while (( $# > 0 )); do
  case "$1" in
    -Root|--root)
      [[ $# -ge 2 ]] || { print -u2 "Missing value for $1"; usage; exit 2; }
      root="$2"
      shift 2
      ;;
    -Prefix|--prefix)
      [[ $# -ge 2 ]] || { print -u2 "Missing value for $1"; usage; exit 2; }
      prefix="$2"
      shift 2
      ;;
    -IncludePath|--include-path)
      [[ $# -ge 2 ]] || { print -u2 "Missing value for $1"; usage; exit 2; }
      include_path="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      print -u2 "Unknown argument: $1"
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$root" ]]; then
  print -u2 "Missing required argument: -Root"
  usage
  exit 2
fi

if [[ ! -d "$root" ]]; then
  print -u2 "Path not found: $root"
  exit 1
fi

resolved_root="$(cd "$root" && pwd -P)"
normalized_prefix=""
if [[ -n "${prefix//[[:space:]]/}" ]]; then
  normalized_prefix="$(normalize_code "${prefix//[[:space:]]/}")"
fi

include_filter="${include_path//\\//}"

typeset -a records
typeset -A code_counts
typeset -A used_codes

while IFS= read -r -d '' file; do
  rel_path="${file#$resolved_root/}"
  rel_filter_path="${rel_path//\\//}"
  full_filter_path="${file//\\//}"

  if [[ -n "$include_filter" && "$rel_filter_path" != *"$include_filter"* && "$full_filter_path" != *"$include_filter"* ]]; then
    continue
  fi

  while IFS=$'\t' read -r line_no raw_code name text; do
    [[ -n "$line_no" ]] || continue

    digits="$(normalize_code "$raw_code")"
    if [[ -n "$normalized_prefix" && "$digits" != ${normalized_prefix}* ]]; then
      continue
    fi

    records+=("${digits}"$'\t'"$(format_code "$digits")"$'\t'"$name"$'\t'"$rel_path"$'\t'"$line_no"$'\t'"$text")
    (( code_counts[$digits] = ${code_counts[$digits]:-0} + 1 ))
    used_codes[$digits]=1
  done < <(
    LC_ALL=en_US.UTF-8 LC_CTYPE=en_US.UTF-8 LANG=en_US.UTF-8 perl -Mutf8 -CS -ne '
      while (/new\s+ReturnCode\s*\(\s*([0-9][0-9_]*)/g) {
        my $code = $1;
        my $name = "";
        $name = $1 if /ReturnCode\s+([A-Z0-9_]+)\s*=/;
        my $text = $_;
        chomp $text;
        $text =~ s/^\s+|\s+$//g;
        $text =~ s/\t/ /g;
        print "$.\t$code\t$name\t$text\n";
      }
    ' "$file"
  )
done < <(find "$resolved_root" -type f -name '*.java' -print0)

print "ReturnCode scan root: $root"
if [[ -n "$include_path" ]]; then
  print "Include path filter: $include_path"
fi
if [[ -n "$prefix" ]]; then
  print "Prefix: $prefix"
fi
print "Matched codes: ${#records}"
print

if (( ${#records} == 0 )); then
  print "No ReturnCode values found."
  exit 0
fi

typeset -a duplicate_codes
for code in ${(k)code_counts}; do
  if (( code_counts[$code] > 1 )); then
    duplicate_codes+=("$code")
  fi
done

if (( ${#duplicate_codes} == 0 )); then
  print "No duplicate ReturnCode values found."
else
  print "Duplicate ReturnCode values:"
  for code in ${(on)duplicate_codes}; do
    print "$(format_code "$code")"
    for record in "${records[@]}"; do
      IFS=$'\t' read -r item_code display_code item_name item_file item_line item_text <<< "$record"
      if [[ "$item_code" == "$code" ]]; then
        label=""
        if [[ -n "$item_name" ]]; then
          label=" $item_name"
        fi
        print "  ${item_file}:${item_line}${label}"
      fi
    done
  done
fi

if [[ -n "$normalized_prefix" ]]; then
  width=3
  max_suffix=-1

  for record in "${records[@]}"; do
    IFS=$'\t' read -r item_code display_code item_name item_file item_line item_text <<< "$record"
    if (( ${#item_code} > ${#normalized_prefix} )); then
      suffix="${item_code:${#normalized_prefix}}"
      if [[ "$suffix" == <-> ]]; then
        (( ${#suffix} > width )) && width=${#suffix}
        (( suffix > max_suffix )) && max_suffix=$suffix
      fi
    fi
  done

  candidate=$(( max_suffix < 0 ? 0 : max_suffix + 1 ))
  while true; do
    candidate_code="${normalized_prefix}$(printf "%0${width}d" "$candidate")"
    if [[ -z "${used_codes[$candidate_code]:-}" ]]; then
      print
      print "Next available in ${prefix}: $(format_code "$candidate_code")"
      break
    fi
    (( candidate++ ))
  done
fi
