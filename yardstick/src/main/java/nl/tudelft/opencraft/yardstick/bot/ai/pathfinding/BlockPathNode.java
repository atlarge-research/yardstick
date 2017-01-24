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

public class BlockPathNode implements PathNode {

    private final Vector3i location;

    private PathNode previous, next;

    private int cost = Integer.MAX_VALUE;

    public BlockPathNode(PathSearch source, Vector3i location) {
        this(source, location, null, null);
    }

    public BlockPathNode(PathSearch source, Vector3i location, PathNode previous, PathNode next) {
        this.location = location;
        this.previous = previous;
        this.next = next;
    }

    public BlockPathNode(Vector3i location, int cost) {
        this.location = location;
        this.cost = cost;
    }

    @Override
    public Vector3i getLocation() {
        return location;
    }

    @Override
    public PathNode getNext() {
        return next;
    }

    @Override
    public PathNode getPrevious() {
        return previous;
    }

    @Override
    public void setNext(PathNode next) {
        this.next = next;
    }

    @Override
    public void setPrevious(PathNode previous) {
        this.previous = previous;
    }

    @Override
    public boolean isStart() {
        return previous == null;
    }

    @Override
    public boolean isEnd() {
        return next == null;
    }

    @Override
    public int getCost() {
        return cost;
    }

    @Override
    public void setCost(int cost) {
        this.cost = cost;
    }

    @Override
    public boolean equals(Object obj) {
        return obj instanceof PathNode && location.equals(((PathNode) obj).getLocation());
    }

    @Override
    public String toString() {
        return location.toString() + " Cost=" + cost ;
    }

    @Override
    public int compareTo(PathNode pathNode) {
        return this.cost - pathNode.getCost();
    }

    @Override
    public int hashCode() {
        return location.hashCode();
    }
}
