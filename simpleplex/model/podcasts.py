"""
Podcast Models

SQLAlchemy ORM definitions for:

* :class:`Podcast`

.. moduleauthor:: Nathan Wright <nathan@simplestation.com>

"""
from datetime import datetime
from sqlalchemy import Table, ForeignKey, Column, sql
from sqlalchemy.types import String, Unicode, UnicodeText, Integer, DateTime, Boolean, Float
from sqlalchemy.orm import mapper, relation, backref, synonym, composite, validates, dynamic_loader, column_property

from simpleplex.model import DeclarativeBase, metadata, DBSession, Author, slugify
from simpleplex.model.media import Media, media, MediaStatus


podcasts = Table('podcasts', metadata,
    Column('id', Integer, autoincrement=True, primary_key=True),
    Column('slug', String(50), unique=True, nullable=False),
    Column('created_on', DateTime, default=datetime.now, nullable=False),
    Column('modified_on', DateTime, default=datetime.now, onupdate=datetime.now, nullable=False),
    Column('title', Unicode(50), nullable=False),
    Column('subtitle', Unicode(255)),
    Column('description', UnicodeText),
    Column('category', Unicode(50)),
    Column('author_name', Unicode(50), nullable=False),
    Column('author_email', Unicode(50), nullable=False),
    Column('explicit', Boolean, default=None),
    Column('copyright', Unicode(50)),
    Column('itunes_url', String(80)),
    Column('feedburner_url', String(80)),
)


class Podcast(object):
    """
    Podcast Metadata

    .. attribute:: id
    .. attribute:: slug

        A unique URL-friendly permalink string for looking up this object.

    .. attribute:: created_on
    .. attribute:: modified_on

    .. attribute:: title
    .. attribute:: subtitle
    .. attribute:: description

    .. attribute:: category

        The `iTunes category <http://www.apple.com/itunes/podcasts/specs.html#categories>`_

        Values with a ``>`` are parsed with special meaning. ``Arts > Design``
        implies that this pertains to the Design subcategory of Arts, and the
        feed markup reflects that.

    .. attribute:: author

        An instance of :class:`simpleplex.model.authors.Author`.
        Although not actually a relation, it is implemented as if it were.
        This was decision was made to make it easier to integrate with
        :class:`simpleplex.model.auth.User` down the road.

    .. attribute:: explicit

        The `iTunes explicit <http://www.apple.com/itunes/podcasts/specs.html#explicit>`_
        value.

            * ``True`` means 'yes'
            * ``None`` means no advisory displays, ie. 'no'
            * ``False`` means 'clean'

    .. attribute:: copyright

    .. attribute:: itunes_url

        Optional iTunes subscribe URL.

    .. attribute:: feedburner_url

        Optional Feedburner URL. If set, requests for this podcast's feed will
        be forwarded to this address -- unless, of course, the request is
        coming from Feedburner.

    .. attribute:: media

        A dynamic loader for :class:`simpleplex.model.media.Media` episodes:
        essentially a preconfigured :class:`sqlalchemy.orm.Query`.

    .. attribute:: media_count

        The number of :class:`simpleplex.model.media.Media` episodes.

    .. attribute:: published_media_count

        The number of :class:`simpleplex.model.media.Media` episodes that are
        currently published.

    """

    def __repr__(self):
        return '<Podcast: %s>' % self.slug

    @validates('slug')
    def validate_slug(self, key, slug):
        return slugify(slug)


mapper(Podcast, podcasts, properties={
    'author': composite(Author,
        podcasts.c.author_name,
        podcasts.c.author_email),
    'media': dynamic_loader(Media, backref='podcast'),
    'media_count':
        column_property(
            sql.select(
                [sql.func.count(media.c.id)],
                sql.and_(
                    media.c.podcast_id == podcasts.c.id,
                    media.c.status.op('&')(int(MediaStatus('trash'))) == 0 # status excludes 'trash'
                )
            ).label('media_count'),
            deferred=True
        ),
    'published_media_count':
        column_property(
            sql.select(
                [sql.func.count(media.c.id)],
                sql.and_(
                    media.c.podcast_id == podcasts.c.id,
                    media.c.status.op('&')(int(MediaStatus('publish'))) == int(MediaStatus('publish')), # status includes 'publish'
                    media.c.status.op('&')(int(MediaStatus('trash'))) == 0, # status excludes 'trash'
                )
            ).label('published_media_count'),
            deferred=True
        )
})
