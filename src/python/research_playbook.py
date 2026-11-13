"""
Research Playbook Loader and Saver

Loads and saves research playbook from MDX file.
"""
import pathlib
from typing import Any, Dict, List

import frontmatter

RESEARCH_PLAYBOOK_PATH = pathlib.Path(__file__).parent / "research_playbook.mdx"


def load() -> Dict[str, Any]:
    """
    Load research playbook from MDX file.

    Returns:
        Dict containing playbook content with metadata and sections.

    Example:
        >>> playbook = load()
        >>> print(playbook['metadata']['version'])
        '1.0.0'
    """
    if not RESEARCH_PLAYBOOK_PATH.exists():
        return create_default_playbook()

    with open(RESEARCH_PLAYBOOK_PATH, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)

    return post.metadata


def save(metadata: Dict[str, Any]) -> None:
    """
    Save research playbook to MDX file.

    Args:
        metadata: Dict containing playbook metadata and sections.

    Example:
        >>> metadata = {'version': '1.0.0', 'funding': {'suggested_tools': ['SEC filings']}}
        >>> save(metadata)
    """
    post = frontmatter.Post("", **metadata)
    with open(RESEARCH_PLAYBOOK_PATH, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(post, sort_keys=False))


def create_default_playbook() -> Dict[str, Any]:
    """
    Create default research playbook structure.

    Returns:
        Dict with default playbook structure.
    """
    return {
        'version': '1.0.0',
        'last_updated': '2026-11-13',
        'description': 'Default research playbook with tool suggestions by claim type.',
        'funding': {
            'suggested_tools': [
                'SEC filings',
                'corporate registries',
                'press releases'
            ],
            'strategies': [
                'Follow SEC Form 10-K for company financials',
                'Use corporate registry for ownership structure',
                'Search press releases for recent announcements'
            ]
        },
        'intellectual_property': {
            'suggested_tools': [
                'USPTO database',
                'WIPO trademark database',
                'ESPA database'
            ],
            'strategies': [
                'Search USPTO for patent applications',
                'Check WIPO for international trademarks',
                'Review ESPA for registered marks'
            ]
        },
        'default_quoting_strategies': [
            'Always include source link',
            'Quote verbatim from primary sources',
            'Provide context for quotes',
            'Distinguish between opinion and fact'
        ],
        'default_depth_escalation_rules': {
            'low_confidence': 1,
            'medium_confidence': 2,
            'high_confidence': 3
        },
        'default_confidence_thresholds': {
            'start': 0.5,
            'continue': 0.7,
            'final': 0.9
        }
    }


def get_tool_suggestions(claim_type: str) -> List[str]:
    """
    Get suggested tools for a specific claim type.

    Args:
        claim_type: Type of claim (e.g., 'funding', 'intellectual_property').

    Returns:
        List of suggested tools for the claim type.

    Example:
        >>> get_tool_suggestions('funding')
        ['SEC filings', 'corporate registries', 'press releases']
    """
    playbook = load()
    sections = playbook.get(claim_type, {})

    return sections.get('suggested_tools', [])


if __name__ == '__main__':
    # Test the playbook functions
    import json

    print("=== Research Playbook Module ===\n")

    # Test creating default playbook
    default = create_default_playbook()
    print("Default playbook created:")
    print(json.dumps(default, indent=2))
    print()

    # Test loading and saving
    print(f"Loading from {RESEARCH_PLAYBOOK_PATH}...")
    loaded = load()
    print(f"Loaded: {loaded.get('version')}")
    print()

    # Test getting tool suggestions
    tools = get_tool_suggestions('funding')
    print(f"Suggested tools for 'funding': {tools}")
