/*
Copyright (c) 2013, DarkStorm (darkstorm@evilminecraft.net)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
package nl.tudelft.opencraft.yardstick.bot.ai.pathfinding;

import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class PathNode implements Comparable<PathNode> {

    private PathNode next;
    private PathNode previous;
    private Vector3i location;
    private int cost = Integer.MAX_VALUE;

    public PathNode(Vector3i location) {
        this.location = location;
    }

    public PathNode(Vector3i location, PathNode previous, PathNode next) {
        this.location = location;
        this.previous = previous;
        this.next = next;
    }

    public Vector3i getLocation() {
        return this.location;
    }

    public PathNode getNext() {
        return this.next;
    }

    public PathNode getPrevious() {
        return this.previous;
    }

    public void setNext(PathNode node) {
        this.next = node;
    }

    public void setPrevious(PathNode node) {
        this.previous = node;
    }

    public int getCost() {
        return this.cost;
    }

    public void setCost(int cost) {
        this.cost = cost;
    }

    public boolean isStart() {
        return this.previous == null;
    }

    public boolean isEnd() {
        return this.next == null;
    }

    @Override
    public int compareTo(PathNode pathNode) {
        return this.cost - pathNode.getCost();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || getClass() != o.getClass()) {
            return false;
        }

        PathNode pathNode = (PathNode) o;

        if (cost != pathNode.cost) {
            return false;
        }
        if (next != null ? !next.equals(pathNode.next) : pathNode.next != null) {
            return false;
        }
        if (previous != null ? !previous.equals(pathNode.previous) : pathNode.previous != null) {
            return false;
        }
        return location.equals(pathNode.location);
    }

    @Override
    public int hashCode() {
        return this.location.hashCode();
    }
}
